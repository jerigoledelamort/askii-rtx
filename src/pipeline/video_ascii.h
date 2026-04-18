#pragma once

#include <string>

class VideoExporter {
public:
	VideoExporter(int width, int height, int fps, const std::string& filename);
	~VideoExporter();

	void add_frame(const float* rgb_data);
	void finish();

private:
	int width, height, fps;
	std::string filename;
	// In a real implementation, would use ffmpeg or imageio
};
