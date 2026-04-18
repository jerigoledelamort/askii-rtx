#pragma once

// Global includes for GLM (vector/matrix math)
// GLM must be installed or included as a header-only library

#define GLM_FORCE_INLINE
#define GLM_FORCE_SSE42
#define GLM_FORCE_DEFAULT_ALIGNED_GENTYPES

#include <glm/glm.hpp>
#include <glm/gtc/matrix_transform.hpp>
#include <glm/gtc/type_ptr.hpp>
#include <glm/gtc/constants.hpp>

// Version info
#define ASCII_RTX_VERSION_MAJOR 1
#define ASCII_RTX_VERSION_MINOR 0
#define ASCII_RTX_VERSION_PATCH 0

#define ASCII_RTX_VERSION "1.0.0"
