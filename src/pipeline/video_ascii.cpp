#include "video_ascii.h"
#include <cstring>

VideoExporter::VideoExporter(int w, int h, int f, const std::string& fn)
	: width(w), height(h), fps(f), filename(fn) {
}

VideoExporter::~VideoExporter() {
}

void VideoExporter::add_frame(const float* rgb_data) {
	// Placeholder: real implementation would encode frame
}

void VideoExporter::finish() {
	// Placeholder: real implementation would finalize video
}
