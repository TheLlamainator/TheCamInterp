#ifdef _WIN32
#define FRUC_API __declspec(dllexport)
#else
#define FRUC_API
#endif

#ifdef __cplusplus
extern "C" {
#endif

typedef enum {
  FRUC_FORMAT_BGR8 = 0
} FrucFormat;

typedef struct {
  int width;
  int height;
  int format;
  int rowStride;
} FrucDesc;

FRUC_API int fruc_init(const FrucDesc* desc);
FRUC_API int fruc_interpolate(const unsigned char* prev,
                              const unsigned char* curr,
                              float t,
                              unsigned char* out);
FRUC_API void fruc_shutdown(void);

#ifdef __cplusplus
}
#endif
