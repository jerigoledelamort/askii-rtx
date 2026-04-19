## Build & Run

### Requirements

* Windows 10/11
* Visual Studio 2022 (MSVC)
* CMake 3.20+
* DirectX 11 (already in Windows SDK)

---

### 1. Clone repository

```bash
git clone https://github.com/your-repo/ascii-rtx.git
cd ascii-rtx
```

---

### 2. Configure build

```bash
cmake -S . -B build ^
  -DASCII_RTX_BUILD_GUI=ON ^
  -DASCII_RTX_BUILD_VIEWER=OFF ^
  -DASCII_RTX_BUILD_INTERACTIVE=OFF
```

---

### 3. Build

```bash
cmake --build build --config Release
```

---

### 4. Run

Executable will be located at:

```
build/Release/ascii_rtx_gui.exe
```

Run:

```bash
build\Release\ascii_rtx_gui.exe
```

---

### Quick run (optional)

You can also use:

```bash
run_gui.bat
```
