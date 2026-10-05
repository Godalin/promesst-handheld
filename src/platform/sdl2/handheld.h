#ifndef PROMESST_HANDHELD_H
#define PROMESST_HANDHELD_H

#include <SDL.h>
#include <assert.h>
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>

typedef unsigned int uint;
#define TRUE 1
#define FALSE 0
enum { STBWINGRAPH_unprocessed = -100, STBWINGRAPH_update_pause = -99 };
enum { STBWGE_create, STBWGE_char, STBWGE_destroy, STBWGE_keydown,
       STBWGE_keyup, STBWGE_deactivate, STBWGE_activate, STBWGE_size, STBWGE_draw };
typedef struct { int type, key, width, height; } stbwingraph_event;
typedef int (*stbwingraph_window_proc)(void *, stbwingraph_event *);
void *stbwingraph_CreateWindow(int, stbwingraph_window_proc, void *, char *, int, int, int, int, int, int);
void stbwingraph_Priority(int);
void stbwingraph_ShowCursor(void *, int);
void stbwingraph_SwapBuffers(void *);
int stbwingraph_MainLoop(int (*)(float, int, int), float);
void stbwingraph_main(void);

/* Only the orthographic, textured rectangle vocabulary used by these games.
 * These are project functions; no OpenGL context or library is used. */
enum { GL_TEXTURE_2D, GL_LIGHTING, GL_DEPTH_TEST, GL_FALSE, GL_COLOR_BUFFER_BIT,
       GL_PROJECTION, GL_SRC_ALPHA, GL_ONE, GL_ONE_MINUS_SRC_ALPHA, GL_BLEND,
       GL_QUADS, GL_ADD };
void glEnable(int);
void glDisable(int);
void glDepthMask(int);
void glMatrixMode(int);
void glLoadIdentity(void);
void glOrtho(double, double, double, double, double, double);
void glViewport(int, int, int, int);
void glClearColor(float, float, float, float);
void glClear(int);
void glBlendFunc(int, int);
void glBindTexture(int, int);
void glBegin(int);
void glEnd(void);
void glColor4ub(unsigned char, unsigned char, unsigned char, unsigned char);
void glColor4ubv(const unsigned char *);
void glColor4f(float, float, float, float);
void glColor3f(float, float, float);
void glTexCoord2f(float, float);
void glVertex2i(int, int);
void glVertex2f(float, float);
int stbgl_TexImage2D(int, int, int, void *, char *);
int stbgl_LoadTexture(char *, char *);

extern SDL_Renderer *hh_renderer;
extern SDL_Texture *hh_canvas;
#define HH_WIDTH 320
#define HH_HEIGHT 240
void hh_render_shutdown(void);
void hh_present(void);
void hh_screenshot(const char *);
void hh_fail(const char *);
char *hh_save_path(void);
FILE *hh_save_open(void);
void hh_save_commit(FILE *);
int hh_load_scale(void);
void hh_store_scale(int);
int hh_button_key(int button, int menu);
void hh_viewport(int width, int height, int integer, SDL_Rect *out);

#endif
