#pragma once

#if defined(_WIN32)
 #ifdef RENDER_BUILD_DLL
  #define RENDER_API __declspec(dllexport)
 #else
  #define RENDER_API __declspec(dllimport)
 #endif
#else
 #define RENDER_API __attribute__((visibility("default")))
#endif