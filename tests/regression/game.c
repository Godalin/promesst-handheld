/* Compile with the local generated source to exercise the original static game
 * routines directly. No source or level data from upstream is stored here. */
#ifdef NDEBUG
#undef NDEBUG
#endif
#include "main.c"

static void equal_world(const gamestate *before) {
    assert(!memcmp(before->tilemap, tilemap, sizeof(tilemap)));
    assert(!memcmp(before->objmap, objmap, sizeof(objmap)));
    assert(px == before->state.player_x && py == before->state.player_y && pz == before->state.player_z);
    assert(state.num_gems == before->state.num_gems);
    assert(state.has_wand == before->state.has_wand);
}

int main(void) {
    restart_game();
    gamestate initial;
    memset(&initial, 0, sizeof(initial));
    save_map(&initial);
    /* Crossing a room boundary records an undo snapshot. Restoring it must
     * restore both world data and the previous player position. */
    int next_room = (room_x + 1) % NUM_X;
    set_player_pos(next_room * SIZE_X, py, pz);
    assert(undo_chain);
    restore_undo();
    equal_world(&initial);
    /* Persistence must retain world, checkpoint and a room undo across restart. */
    checkpoint = initial;
    set_player_pos(next_room * SIZE_X, py, pz);
    gamestate current;
    memset(&current, 0, sizeof(current));
    save_map(&current);
    game_started = 1;
    save_game();
    flush_undo();
    restart_game();
    load_game();
    equal_world(&current);
    assert(!memcmp(&checkpoint, &initial, sizeof(initial)));
    assert(undo_chain);
    restore_undo();
    equal_world(&initial);
    /* Incomplete data may not mutate a live world or mark a game as loaded. */
    FILE *bad = fopen(get_savegame_path(), "wb");
    assert(bad); fputs("broken", bad); fclose(bad);
    game_started = 0;
    load_game();
    assert(!game_started);
    equal_world(&initial);
    /* Physical controls include the second game's third action and menu confirm. */
    assert(hh_button_key(SDL_CONTROLLER_BUTTON_A, 0) == 'z');
    assert(hh_button_key(SDL_CONTROLLER_BUTTON_A, 1) == '\r');
    assert(hh_button_key(SDL_CONTROLLER_BUTTON_B, 0) == 'x');
    assert(hh_button_key(SDL_CONTROLLER_BUTTON_X, 0) == 'c');
    assert(hh_button_key(SDL_CONTROLLER_BUTTON_RIGHTSHOULDER, 0) == 8);
    SDL_Rect fit;
    hh_viewport(720, 720, 1, &fit);
    assert(fit.x == 40 && fit.y == 120 && fit.w == 640 && fit.h == 480);
    hh_viewport(720, 720, 0, &fit);
    assert(fit.x == 0 && fit.y == 90 && fit.w == 720 && fit.h == 540);
    hh_viewport(240, 160, 1, &fit);
    assert(fit.w == 213 && fit.h == 160);
    flush_undo();
    puts(HH_GAME ": world undo, save/reload, checkpoint, corrupt save, controls and square viewport passed");
    return 0;
}
