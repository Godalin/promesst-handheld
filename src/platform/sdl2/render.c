#include "handheld.h"

typedef struct { SDL_Texture *texture; int width, height; } Image;
static Image images[8];
static int image_count, bound, vertices;
static SDL_Rect viewport = {0, 0, HH_WIDTH, HH_HEIGHT};
static double left, top, right = 800, bottom = 600;
static Uint8 tint[4] = {255, 255, 255, 255};
static SDL_BlendMode blend = SDL_BLENDMODE_BLEND;
static float uv[2], points[4][4];
extern unsigned char *stbi_load(char const *, int *, int *, int *, int);

void hh_fail(const char *message) {
    fprintf(stderr, "%s: %s\n", message, SDL_GetError());
    exit(1);
}

void hh_viewport(int w, int h, int integer, SDL_Rect *out) {
    double scale = fmin(w / (double)HH_WIDTH, h / (double)HH_HEIGHT);
    if (integer && scale >= 1) scale = floor(scale);
    out->w = (int)lround(HH_WIDTH * scale);
    out->h = (int)lround(HH_HEIGHT * scale);
    out->x = (w - out->w) / 2;
    out->y = (h - out->h) / 2;
}

void glEnable(int unused) { (void)unused; }
void glDisable(int unused) { (void)unused; }
void glDepthMask(int unused) { (void)unused; }
void glMatrixMode(int unused) { (void)unused; }
void glLoadIdentity(void) {}
void glOrtho(double l, double r, double b, double t, double near, double far) {
    (void)near; (void)far; left = l; right = r; top = t; bottom = b;
}
void glViewport(int x, int y, int w, int h) {
    viewport = (SDL_Rect){x, HH_HEIGHT - y - h, w, h};
}
void glClearColor(float r, float g, float b, float a) {
    (void)r; (void)g; (void)b; (void)a;
}
void glClear(int unused) {
    (void)unused;
    SDL_SetRenderTarget(hh_renderer, hh_canvas);
    SDL_RenderSetViewport(hh_renderer, NULL);
    SDL_SetRenderDrawColor(hh_renderer, 0, 0, 0, 255);
    SDL_RenderClear(hh_renderer);
}
void glBlendFunc(int source, int destination) {
    (void)source;
    blend = (destination == GL_ONE || destination == GL_ADD) ? SDL_BLENDMODE_ADD : SDL_BLENDMODE_BLEND;
}
void glBindTexture(int unused, int id) { (void)unused; bound = id; }
void glBegin(int unused) { (void)unused; vertices = 0; }
void glEnd(void) { assert(vertices == 0); }
void glColor4ub(Uint8 r, Uint8 g, Uint8 b, Uint8 a) {
    tint[0] = r; tint[1] = g; tint[2] = b; tint[3] = a;
}
void glColor4ubv(const Uint8 *c) { glColor4ub(c[0], c[1], c[2], c[3]); }
static Uint8 channel(float v) { return (Uint8)lroundf(fmaxf(0, fminf(1, v)) * 255); }
void glColor4f(float r, float g, float b, float a) { glColor4ub(channel(r), channel(g), channel(b), channel(a)); }
void glColor3f(float r, float g, float b) { glColor4f(r, g, b, 1); }
void glTexCoord2f(float s, float t) { uv[0] = s; uv[1] = t; }

/* Split texture wrapping at integer UV boundaries, also preserving flips.
 * In-game tiles normally need a single copy; the animated menu wraps its atlas. */
static int splits(double a, double b, double *values) {
    int count = 0;
    values[count++] = 0;
    if (b > a) {
        for (double edge = floor(a) + 1; edge < b && count < 30; edge++)
            values[count++] = (edge - a) / (b - a);
    } else if (b < a) {
        for (double edge = ceil(a) - 1; edge > b && count < 30; edge--)
            values[count++] = (edge - a) / (b - a);
    }
    values[count++] = 1;
    return count;
}

static void quad(void) {
    if (bound <= 0 || bound > image_count) hh_fail("Invalid texture");
    Image *image = &images[bound - 1];
    double x0 = viewport.x + (points[0][0] - left) * viewport.w / (right - left);
    double x1 = viewport.x + (points[2][0] - left) * viewport.w / (right - left);
    double y0 = viewport.y + (points[0][1] - top) * viewport.h / (bottom - top);
    double y1 = viewport.y + (points[2][1] - top) * viewport.h / (bottom - top);
    double s0 = points[0][2], s1 = points[2][2], t0 = points[0][3], t1 = points[2][3];
    double xs[32], ys[32];
    int nx = splits(s0, s1, xs), ny = splits(t0, t1, ys);
    SDL_SetTextureColorMod(image->texture, tint[0], tint[1], tint[2]);
    SDL_SetTextureAlphaMod(image->texture, tint[3]);
    SDL_SetTextureBlendMode(image->texture, blend);
    SDL_RenderSetClipRect(hh_renderer, &viewport);
    for (int y = 0; y < ny - 1; y++) for (int x = 0; x < nx - 1; x++) {
        double sa = s0 + (s1 - s0) * xs[x], sb = s0 + (s1 - s0) * xs[x + 1];
        double ta = t0 + (t1 - t0) * ys[y], tb = t0 + (t1 - t0) * ys[y + 1];
        double so = floor((sa + sb) / 2), to = floor((ta + tb) / 2);
        int sx0 = (int)lround((fmin(sa, sb) - so) * image->width);
        int sx1 = (int)lround((fmax(sa, sb) - so) * image->width);
        int sy0 = (int)lround((fmin(ta, tb) - to) * image->height);
        int sy1 = (int)lround((fmax(ta, tb) - to) * image->height);
        int dx0 = (int)lround(x0 + (x1 - x0) * xs[x]);
        int dx1 = (int)lround(x0 + (x1 - x0) * xs[x + 1]);
        int dy0 = (int)lround(y0 + (y1 - y0) * ys[y]);
        int dy1 = (int)lround(y0 + (y1 - y0) * ys[y + 1]);
        SDL_Rect src = {sx0, sy0, sx1 - sx0, sy1 - sy0};
        SDL_Rect dst = {dx0, dy0, dx1 - dx0, dy1 - dy0};
        SDL_RendererFlip flip = SDL_FLIP_NONE;
        if (sb < sa) flip = (SDL_RendererFlip)(flip | SDL_FLIP_HORIZONTAL);
        if (tb < ta) flip = (SDL_RendererFlip)(flip | SDL_FLIP_VERTICAL);
        if (src.w > 0 && src.h > 0 && dst.w > 0 && dst.h > 0)
            if (SDL_RenderCopyEx(hh_renderer, image->texture, &src, &dst, 0, NULL, flip) < 0)
                hh_fail("Texture rendering failed");
    }
    SDL_RenderSetClipRect(hh_renderer, NULL);
}
void glVertex2f(float x, float y) {
    points[vertices][0] = x; points[vertices][1] = y;
    points[vertices][2] = uv[0]; points[vertices][3] = uv[1];
    if (++vertices == 4) { quad(); vertices = 0; }
}
void glVertex2i(int x, int y) { glVertex2f(x, y); }

int stbgl_TexImage2D(int id, int w, int h, void *data, char *options) {
    (void)options;
    if (id || !data || w <= 0 || h <= 0 || image_count == 8) hh_fail("Invalid image");
    SDL_Surface *surface = SDL_CreateRGBSurfaceFrom(data, w, h, 32, w * 4,
        0x000000ff, 0x0000ff00, 0x00ff0000, 0xff000000);
    if (!surface) hh_fail("Image surface creation failed");
    SDL_Texture *texture = SDL_CreateTextureFromSurface(hh_renderer, surface);
    SDL_FreeSurface(surface);
    if (!texture) hh_fail("Image texture creation failed");
    images[image_count++] = (Image){texture, w, h};
    return image_count;
}
int stbgl_LoadTexture(char *path, char *options) {
    int w, h, components;
    unsigned char *pixels = stbi_load(path, &w, &h, &components, 4);
    if (!pixels) { fprintf(stderr, "Missing/invalid resource: %s\n", path); exit(1); }
    int id = stbgl_TexImage2D(0, w, h, pixels, options);
    free(pixels);
    return id;
}
void hh_screenshot(const char *path) {
    int w, h;
    SDL_GetRendererOutputSize(hh_renderer, &w, &h);
    SDL_Surface *surface = SDL_CreateRGBSurfaceWithFormat(0, w, h, 32, SDL_PIXELFORMAT_ARGB8888);
    if (!surface || SDL_RenderReadPixels(hh_renderer, NULL, surface->format->format, surface->pixels, surface->pitch) < 0)
        hh_fail("Screenshot capture failed");
    if (SDL_SaveBMP(surface, path) < 0) hh_fail("Screenshot write failed");
    SDL_FreeSurface(surface);
}
void hh_render_shutdown(void) {
    for (int i = 0; i < image_count; i++) SDL_DestroyTexture(images[i].texture);
    image_count = 0;
}
