#include "fruc.h"
#include <cstring>

// Placeholder implementation: "blend" only.
// Later: replace with NVIDIA Optical Flow FRUC (GPU).
static FrucDesc g_desc;

extern "C" {

int fruc_init(const FrucDesc* desc) {
    if (!desc || desc->width <= 0 || desc->height <= 0) return 1;
    g_desc = *desc;
    return 0;
}

int fruc_interpolate(const unsigned char* prev,
                     const unsigned char* curr,
                     float t,
                     unsigned char* out) {
    if (!prev || !curr || !out) return 2;
    const int bytes = g_desc.height * g_desc.rowStride;
    // naive 50/50 blend (MVP placeholder)
    for (int i = 0; i < bytes; ++i) {
        out[i] = (unsigned char)(((int)prev[i] + (int)curr[i]) / 2);
    }
    return 0;
}

void fruc_shutdown(void) {
    // nothing yet
}

} // extern "C"
