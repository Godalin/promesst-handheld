#define _POSIX_C_SOURCE 200809L
#include "handheld.h"
#include <errno.h>
#include <limits.h>
#include <sys/stat.h>
#include <unistd.h>

static char save_path[PATH_MAX], temporary[PATH_MAX];

static int scale_path(char *path, size_t size) {
    const char *directory = getenv("PROMESST_CONFIG_DIR");
    char *fallback = NULL;
    if (!directory || !*directory) { fallback = SDL_GetPrefPath("SilverSpaceship", HH_GAME); directory = fallback; }
    int valid = directory && snprintf(path, size, "%s/scale.txt", directory) < (int)size;
    SDL_free(fallback);
    return valid;
}
int hh_load_scale(void) {
    char path[PATH_MAX]; int scale = 1;
    if (!scale_path(path, sizeof(path))) return scale;
    FILE *f = fopen(path, "r");
    if (f) { int value; if (fscanf(f, "%d", &value) == 1 && (value == 0 || value == 1)) scale = value; fclose(f); }
    return scale;
}
void hh_store_scale(int scale) {
    char path[PATH_MAX];
    if (!scale_path(path, sizeof(path))) return;
    FILE *f = fopen(path, "w");
    if (f) { fprintf(f, "%d\n", !!scale); fclose(f); }
}

char *hh_save_path(void) {
    if (!save_path[0]) {
        const char *directory = getenv("PROMESST_SAVE_DIR");
        char *fallback = NULL;
        if (!directory || !*directory) {
            fallback = SDL_GetPrefPath("SilverSpaceship", HH_GAME);
            directory = fallback;
        }
        if (!directory || snprintf(save_path, sizeof(save_path), "%s/save.dat", directory) >= (int)sizeof(save_path)) {
            fprintf(stderr, "Invalid save directory\n"); exit(1);
        }
        SDL_free(fallback);
        for (char *p = save_path + 1; *p; p++) if (*p == '/') {
            *p = 0;
            if (mkdir(save_path, 0755) < 0 && errno != EEXIST) { perror(save_path); exit(1); }
            *p = '/';
        }
        if (snprintf(temporary, sizeof(temporary), "%s.tmp", save_path) >= (int)sizeof(temporary)) exit(1);
    }
    return save_path;
}
FILE *hh_save_open(void) {
    hh_save_path();
    FILE *file = fopen(temporary, "wb");
    if (!file) perror(temporary);
    return file;
}
void hh_save_commit(FILE *file) {
    int failed = ferror(file);
    if (fflush(file) != 0) failed = 1;
    if (fsync(fileno(file)) != 0) failed = 1;
    if (fclose(file) != 0) failed = 1;
    if (!failed && rename(temporary, save_path) == 0) return;
    fprintf(stderr, "Save write failed; previous save retained: %s\n", save_path);
    unlink(temporary);
}
