cmake_minimum_required(VERSION 3.10)
project(promesst_handheld C)
set(CMAKE_C_STANDARD 99)
set(CMAKE_C_STANDARD_REQUIRED ON)
find_package(PkgConfig REQUIRED)
pkg_check_modules(SDL2 REQUIRED IMPORTED_TARGET sdl2>=2.0.8)
find_package(PythonInterp 3 REQUIRED)
option(HH_SANITIZERS "Enable address and undefined-behavior sanitizers" OFF)
if(HH_SANITIZERS)
  add_compile_options(-fsanitize=address,undefined -fno-omit-frame-pointer -g)
  set(CMAKE_EXE_LINKER_FLAGS "${CMAKE_EXE_LINKER_FLAGS} -fsanitize=address,undefined")
endif()
set(GENERATED "${CMAKE_CURRENT_BINARY_DIR}/generated")
execute_process(COMMAND "${PYTHON_EXECUTABLE}" "${CMAKE_SOURCE_DIR}/scripts/prepare_sources.py"
  --output "${GENERATED}" RESULT_VARIABLE PREPARE_RESULT)
if(NOT PREPARE_RESULT EQUAL 0)
  message(FATAL_ERROR "Upstream import/source adaptation failed")
endif()
execute_process(COMMAND "${PYTHON_EXECUTABLE}" "${CMAKE_SOURCE_DIR}/scripts/prepare_sources.py"
  --baseline --output "${CMAKE_CURRENT_BINARY_DIR}/reference" RESULT_VARIABLE REFERENCE_RESULT)
if(NOT REFERENCE_RESULT EQUAL 0)
  message(FATAL_ERROR "Original reference preparation failed")
endif()
set_property(DIRECTORY APPEND PROPERTY CMAKE_CONFIGURE_DEPENDS
  "${CMAKE_SOURCE_DIR}/scripts/prepare_sources.py"
  "${CMAKE_SOURCE_DIR}/upstream/promesst/source/main.c"
  "${CMAKE_SOURCE_DIR}/upstream/promesst2/source/main.c")
set(PLATFORM
  src/platform/sdl2/render.c
  src/platform/sdl2/runtime.c
  src/platform/storage/storage.c)
enable_testing()
foreach(GAME promesst promesst2)
  if(GAME STREQUAL "promesst")
    set(SAVE_MAGIC "PMSTHH01")
  else()
    set(SAVE_MAGIC "PMSTHH02")
  endif()
  add_executable(${GAME} "${GENERATED}/${GAME}/main.c" ${PLATFORM})
  target_include_directories(${GAME} PRIVATE src/platform/sdl2)
  target_compile_definitions(${GAME} PRIVATE HH_GAME="${GAME}" HH_SAVE_MAGIC="${SAVE_MAGIC}")
  target_compile_options(${GAME} PRIVATE -Wall -Wno-unused-variable -Wno-unused-function -Wno-sign-compare
    -Wno-misleading-indentation -Wno-missing-braces)
  target_link_libraries(${GAME} PRIVATE PkgConfig::SDL2 m)
  add_executable(${GAME}_regression tests/regression/game.c ${PLATFORM})
  target_include_directories(${GAME}_regression PRIVATE "${GENERATED}/${GAME}" src/platform/sdl2)
  target_compile_definitions(${GAME}_regression PRIVATE HH_NO_MAIN HH_GAME="${GAME}" HH_SAVE_MAGIC="${SAVE_MAGIC}")
  target_link_libraries(${GAME}_regression PRIVATE PkgConfig::SDL2 m)
  add_test(NAME ${GAME}_regression COMMAND ${GAME}_regression)
  set_tests_properties(${GAME}_regression PROPERTIES ENVIRONMENT
    "PROMESST_SAVE_DIR=${CMAKE_CURRENT_BINARY_DIR}/test-saves/${GAME}"
    WORKING_DIRECTORY "${CMAKE_SOURCE_DIR}/assets/${GAME}")
  add_executable(${GAME}_reference "${CMAKE_CURRENT_BINARY_DIR}/reference/${GAME}/main.c" ${PLATFORM})
  target_include_directories(${GAME}_reference PRIVATE src/platform/sdl2)
  target_compile_definitions(${GAME}_reference PRIVATE HH_GAME="${GAME}" HH_SAVE_MAGIC="${SAVE_MAGIC}")
  target_link_libraries(${GAME}_reference PRIVATE PkgConfig::SDL2 m)
endforeach()
