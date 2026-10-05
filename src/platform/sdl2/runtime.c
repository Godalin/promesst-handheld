#define _POSIX_C_SOURCE 200809L
#include "handheld.h"
#include <signal.h>
#include <unistd.h>

SDL_Renderer *hh_renderer;
SDL_Texture *hh_canvas;
static SDL_Window *window;
static SDL_GameController *controller;
static stbwingraph_window_proc callback;
static void *callback_data;
static volatile sig_atomic_t quitting;
static int integer_scale = 1, fullscreen = 1, frames = -1, frame;
static int window_width = 720, window_height = 720;
static int queue[64], queue_read, queue_write;
static int previous_direction, repeat_at;
static const char *capture_path, *input_script, *report_path;
static FILE *report;
extern int main_mode, queued_key;
extern void hh_report(FILE *, int);
extern void hh_game_cleanup(void);

static void event(int type, int key) {
    stbwingraph_event e = {type, key, HH_WIDTH, HH_HEIGHT};
    callback(callback_data, &e);
}
static void enqueue(int key) {
    int next = (queue_write + 1) % 64;
    if (next != queue_read) { queue[queue_write] = key; queue_write = next; }
}
static void signal_exit(int signal_number) { (void)signal_number; quitting = 1; }

int hh_button_key(int button, int menu) {
    switch (button) {
        case SDL_CONTROLLER_BUTTON_A: return menu ? '\r' : 'z';
        case SDL_CONTROLLER_BUTTON_B: return menu ? 27 : 'x';
        case SDL_CONTROLLER_BUTTON_X: return menu ? 27 : 'c';
        case SDL_CONTROLLER_BUTTON_RIGHTSHOULDER: return 8;
        case SDL_CONTROLLER_BUTTON_START: return 27;
        case SDL_CONTROLLER_BUTTON_DPAD_UP: return 'w';
        case SDL_CONTROLLER_BUTTON_DPAD_DOWN: return 's';
        case SDL_CONTROLLER_BUTTON_DPAD_LEFT: return 'a';
        case SDL_CONTROLLER_BUTTON_DPAD_RIGHT: return 'd';
        default: return 0;
    }
}
static int directional(int key) { return key == 'w' || key == 'a' || key == 's' || key == 'd'; }
static int keyboard_key(SDL_Keycode key) {
    switch (key) {
        case SDLK_UP: return 'w'; case SDLK_DOWN: return 's';
        case SDLK_LEFT: return 'a'; case SDLK_RIGHT: return 'd';
        case SDLK_RETURN: return '\r'; case SDLK_BACKSPACE: return 8;
        case SDLK_ESCAPE: return 27;
        default: return key > 0 && key < 128 ? (int)key : 0;
    }
}
static void open_controller(void) {
    if (getenv("PROMESST_KEYBOARD_ONLY")) return;
    if (!SDL_WasInit(SDL_INIT_GAMECONTROLLER)) return;
    if (controller) return;
    for (int i = 0; i < SDL_NumJoysticks(); i++) if (SDL_IsGameController(i)) {
        controller = SDL_GameControllerOpen(i);
        if (controller) {
            fprintf(stderr, "Controller: %s\n", SDL_GameControllerName(controller));
            return;
        }
    }
}
static int controller_direction(void) {
    if (!controller) return 0;
    int buttons[] = {SDL_CONTROLLER_BUTTON_DPAD_UP, SDL_CONTROLLER_BUTTON_DPAD_DOWN,
                     SDL_CONTROLLER_BUTTON_DPAD_LEFT, SDL_CONTROLLER_BUTTON_DPAD_RIGHT};
    for (int i = 0; i < 4; i++) if (SDL_GameControllerGetButton(controller, buttons[i]))
        return hh_button_key(buttons[i], 0);
    int x = SDL_GameControllerGetAxis(controller, SDL_CONTROLLER_AXIS_LEFTX);
    int y = SDL_GameControllerGetAxis(controller, SDL_CONTROLLER_AXIS_LEFTY);
    if (abs(x) > 16000 && abs(x) > abs(y)) return x < 0 ? 'a' : 'd';
    if (abs(y) > 16000) return y < 0 ? 'w' : 's';
    return 0;
}
static void process_events(void) {
    SDL_Event e;
    while (SDL_PollEvent(&e)) {
        switch (e.type) {
            case SDL_QUIT: quitting = 1; break;
            case SDL_WINDOWEVENT:
                if (e.window.event == SDL_WINDOWEVENT_CLOSE) quitting = 1;
                if (e.window.event == SDL_WINDOWEVENT_FOCUS_LOST) {
                    queue_read = queue_write;
                    previous_direction = 0;
                }
                break;
            case SDL_CONTROLLERDEVICEADDED: open_controller(); break;
            case SDL_CONTROLLERDEVICEREMOVED:
                if (controller && !SDL_GameControllerGetAttached(controller)) {
                    SDL_GameControllerClose(controller); controller = NULL;
                    previous_direction = 0; open_controller();
                }
                break;
            case SDL_KEYDOWN: {
                if (e.key.keysym.sym == SDLK_F2 && !e.key.repeat) {
                    integer_scale = !integer_scale; hh_store_scale(integer_scale); break;
                }
                if (e.key.keysym.sym == SDLK_F4 && (e.key.keysym.mod & KMOD_ALT)) { quitting = 1; break; }
                int key = keyboard_key(e.key.keysym.sym);
                if (key && (!e.key.repeat || directional(key))) enqueue(key);
                break;
            }
            case SDL_CONTROLLERBUTTONDOWN: {
                if (getenv("PROMESST_KEYBOARD_ONLY")) break;
                if (e.cbutton.button == SDL_CONTROLLER_BUTTON_Y) { integer_scale = !integer_scale; hh_store_scale(integer_scale); break; }
                int key = hh_button_key(e.cbutton.button, main_mode != 3);
                if (key && !directional(key)) enqueue(key);
                break;
            }
        }
    }
    if (controller && SDL_GameControllerGetButton(controller, SDL_CONTROLLER_BUTTON_BACK)
                   && SDL_GameControllerGetButton(controller, SDL_CONTROLLER_BUTTON_START)) {
        quitting = 1; return;
    }
    int direction = controller_direction(), now = (int)SDL_GetTicks();
    if (direction != previous_direction) {
        previous_direction = direction; repeat_at = now + 300;
        if (direction) enqueue(direction);
    } else if (direction && now >= repeat_at) {
        if (queue_read == queue_write && !queued_key) enqueue(direction);
        repeat_at = now + 120;
    }
}

void *stbwingraph_CreateWindow(int primary, stbwingraph_window_proc proc, void *data,
        char *title, int width, int height, int full, int resize, int alpha, int stencil) {
    (void)primary; (void)width; (void)height; (void)full; (void)resize; (void)alpha; (void)stencil;
    Uint32 subsystems = SDL_INIT_VIDEO | SDL_INIT_EVENTS | SDL_INIT_TIMER;
    if (!getenv("SDL_VIDEODRIVER") || strcmp(getenv("SDL_VIDEODRIVER"), "dummy"))
        subsystems |= SDL_INIT_GAMECONTROLLER;
    if (SDL_Init(subsystems) < 0)
        hh_fail("SDL initialization failed");
    SDL_SetHint(SDL_HINT_RENDER_SCALE_QUALITY, "0");
    Uint32 flags = SDL_WINDOW_SHOWN | SDL_WINDOW_RESIZABLE;
    if (fullscreen) flags |= SDL_WINDOW_FULLSCREEN_DESKTOP;
    window = SDL_CreateWindow(title, SDL_WINDOWPOS_CENTERED, SDL_WINDOWPOS_CENTERED, window_width, window_height, flags);
    if (!window) hh_fail("Window creation failed");
    hh_renderer = SDL_CreateRenderer(window, -1, SDL_RENDERER_ACCELERATED | SDL_RENDERER_TARGETTEXTURE);
    if (!hh_renderer) hh_renderer = SDL_CreateRenderer(window, -1, SDL_RENDERER_SOFTWARE | SDL_RENDERER_TARGETTEXTURE);
    if (!hh_renderer) hh_fail("Renderer creation failed");
    SDL_RendererInfo info;
    SDL_GetRendererInfo(hh_renderer, &info);
    fprintf(stderr, "%s: SDL renderer=%s, logical=%dx%d\n", HH_GAME, info.name, HH_WIDTH, HH_HEIGHT);
    hh_canvas = SDL_CreateTexture(hh_renderer, SDL_PIXELFORMAT_ARGB8888, SDL_TEXTUREACCESS_TARGET, HH_WIDTH, HH_HEIGHT);
    if (!hh_canvas) hh_fail("Canvas creation failed");
    SDL_SetTextureBlendMode(hh_canvas, SDL_BLENDMODE_NONE);
    callback = proc; callback_data = data;
    event(STBWGE_create, 0); event(STBWGE_size, 0);
    open_controller();
    if (!controller && SDL_NumJoysticks() > 0 && !getenv("PROMESST_KEYBOARD_ONLY")) {
        fprintf(stderr, "No mapped SDL controller; requesting PortMaster keyboard fallback\n");
        exit(78);
    }
    return window;
}
void stbwingraph_Priority(int unused) { (void)unused; }
void stbwingraph_ShowCursor(void *unused, int visible) { (void)unused; SDL_ShowCursor(visible); }
void hh_present(void) {
    SDL_SetRenderTarget(hh_renderer, NULL);
    SDL_RenderSetViewport(hh_renderer, NULL);
    SDL_RenderSetClipRect(hh_renderer, NULL);
    SDL_SetRenderDrawColor(hh_renderer, 0, 0, 0, 255); SDL_RenderClear(hh_renderer);
    int w, h; SDL_Rect destination;
    SDL_GetRendererOutputSize(hh_renderer, &w, &h);
    hh_viewport(w, h, integer_scale, &destination);
    SDL_RenderCopy(hh_renderer, hh_canvas, NULL, &destination);
    if (capture_path && frame == frames - 1) hh_screenshot(capture_path);
    SDL_RenderPresent(hh_renderer);
}
void stbwingraph_SwapBuffers(void *unused) { (void)unused; hh_present(); }

static void scripted_input(void) {
    if (!input_script || !*input_script) return;
    while (*input_script) {
        char *end;
        long at = strtol(input_script, &end, 10);
        if (end == input_script || *end != ':') { fprintf(stderr, "Invalid --input frame\n"); exit(2); }
        if (at > frame) return;
        const char *value = end + 1;
        const char *separator = strchr(value, ',');
        size_t length = separator ? (size_t)(separator - value) : strlen(value);
        char name[32];
        if (!length || length >= sizeof(name)) exit(2);
        memcpy(name, value, length); name[length] = 0;
        if (!strcmp(name, "quit")) quitting = 1;
        else {
            int key = 0;
            if (!strcmp(name, "enter")) key = '\r';
            else if (!strcmp(name, "undo")) key = 8;
            else if (!strcmp(name, "menu")) key = 27;
            else if (!strcmp(name, "south")) key = hh_button_key(SDL_CONTROLLER_BUTTON_A, main_mode != 3);
            else if (!strcmp(name, "east")) key = hh_button_key(SDL_CONTROLLER_BUTTON_B, main_mode != 3);
            else if (!strcmp(name, "west")) key = hh_button_key(SDL_CONTROLLER_BUTTON_X, main_mode != 3);
            else if (length == 1 && strchr("wasdzxc", name[0])) key = name[0];
            if (!key) { fprintf(stderr, "Invalid --input action\n"); exit(2); }
            enqueue(key);
        }
        input_script = separator ? separator + 1 : value + length;
    }
}
int stbwingraph_MainLoop(int (*update)(float, int, int), float minimum) {
    if (report_path) { report = fopen(report_path, "w"); if (!report) { perror(report_path); exit(1); } }
    Uint32 previous = SDL_GetTicks();
    while (!quitting && (frames < 0 || frame < frames)) {
        process_events(); scripted_input();
        if (!queued_key && queue_read != queue_write) {
            int key = queue[queue_read]; queue_read = (queue_read + 1) % 64;
            if (main_mode != 3 && key == 'z') key = '\r';
            event(STBWGE_char, key);
        }
        Uint32 now = SDL_GetTicks();
        float dt = frames >= 0 ? 0.016f : (now - previous) / 1000.0f;
        if (frames < 0 && dt < minimum) { SDL_Delay(1); continue; }
        previous = now;
        if (!quitting) update(dt, 1, 1);
        if (report) hh_report(report, frame);
        frame++;
    }
    event(STBWGE_destroy, 0);
    if (report) fclose(report);
    return 0;
}

#ifndef HH_NO_MAIN
int main(int argc, char **argv) {
    integer_scale = hh_load_scale();
    for (int i = 1; i < argc; i++) {
        if (!strcmp(argv[i], "--windowed")) fullscreen = 0;
        else if (!strcmp(argv[i], "--fullscreen")) fullscreen = 1;
        else if (!strcmp(argv[i], "--fit")) integer_scale = 0;
        else if (!strcmp(argv[i], "--integer")) integer_scale = 1;
        else if (!strcmp(argv[i], "--size") && i + 1 < argc) {
            char tail;
            if (sscanf(argv[++i], "%dx%d%c", &window_width, &window_height, &tail) != 2
                || window_width < 160 || window_height < 120 || window_width > 4096 || window_height > 4096) return 2;
        }
        else if (!strcmp(argv[i], "--headless")) { SDL_setenv("SDL_VIDEODRIVER", "dummy", 1); fullscreen = 0; }
        else if (!strcmp(argv[i], "--frames") && i + 1 < argc) {
            char *end; long count = strtol(argv[++i], &end, 10);
            if (*end || count < 1 || count > 1000000) return 2;
            frames = (int)count;
        }
        else if (!strcmp(argv[i], "--screenshot") && i + 1 < argc) capture_path = argv[++i];
        else if (!strcmp(argv[i], "--input") && i + 1 < argc) input_script = argv[++i];
        else if (!strcmp(argv[i], "--report") && i + 1 < argc) report_path = argv[++i];
        else if (!strcmp(argv[i], "--help")) {
            puts("--fullscreen --windowed --size WxH --integer --fit --headless --frames N --screenshot BMP --input FRAME:ACTION,... --report JSONL");
            return 0;
        } else { fprintf(stderr, "Unknown or incomplete argument: %s\n", argv[i]); return 2; }
    }
    if (capture_path && frames < 0) { fprintf(stderr, "--screenshot requires --frames\n"); return 2; }
    const char *assets = getenv("PROMESST_ASSET_DIR");
    if (assets && chdir(assets) != 0) { perror(assets); return 1; }
    signal(SIGTERM, signal_exit); signal(SIGINT, signal_exit);
    stbwingraph_main();
    hh_game_cleanup();
    hh_render_shutdown();
    SDL_DestroyTexture(hh_canvas); SDL_DestroyRenderer(hh_renderer);
    if (controller) SDL_GameControllerClose(controller);
    SDL_DestroyWindow(window); SDL_Quit();
    return 0;
}
#endif
