# Desktop Overlay

A lightweight desktop overlay application that allows you to display images and GIFs on top of all windows. Perfect for displaying reference images, memes, or any visual content while working.

## Features

- **Image & GIF Support** - Display static images (PNG, JPG, JPEG) or animated GIFs
- **Always On Top** - Overlays stay above all other windows
- **Rotate & Resize** - Easily rotate and scale your overlays
- **Drag to Move** - Click and drag to reposition overlays anywhere on screen
- **Opacity Control** - Adjust transparency from 10% to 100%
- **Click-Through Mode** - Make overlays transparent to mouse clicks
- **Multiple Overlays** - Add as many overlays as you want
- **Z-Order Control** - Drag items in the list to control which overlay is on top
- **Save & Load Layouts** - Save your overlay positions and settings
- **Auto-Start** - Option to run at Windows startup
- **Auto-Load** - Automatically load your saved layout on startup
- **System Tray** - Runs quietly in the background

## Installation

### Option 1: Download Pre-built Executable
1. Download the latest release from the [Releases](../../releases) page
2. Run `DesktopOverlay.exe`

### Option 2: Run from Source
1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/desktop-overlay.git
   cd desktop-overlay
   ```

2. Install dependencies:
   ```bash
   pip install PyQt5
   ```

3. Run the application:
   ```bash
   python overlay.py
   ```

## Usage

### Adding an Overlay

1. **Choose Image/GIF** - Click to select an image file
2. **Adjust Settings** (optional):
   - Drag the opacity slider to change transparency
   - Check "Click-through mode" to interact with windows behind the overlay
3. **Add New Overlay** - Click to create the overlay on your desktop

### Controlling Overlays

**Moving:**
- Click and drag the overlay to move it

**Resizing:**
- Hold **Left Mouse Button** + **Scroll Wheel** to resize

**Rotating:**
- Hold **Right Mouse Button** + **Scroll Wheel** to rotate

### Managing Multiple Overlays

- **Active Overlays List** - Shows all current overlays with thumbnails
- **Drag to Reorder** - Drag items in the list to control z-order (top = front)
- **Remove Selected** - Select an overlay and click to remove it
- **Remove All** - Clear all overlays at once

### Saving Your Layout

1. **Save Layout** - Saves all overlay positions, sizes, rotations, and settings
2. **Load Layout** - Restores your saved layout
3. **Auto-load on startup** - Check to automatically load layout when app starts

### Startup Options

- **Run at Windows startup** - Automatically start the app when Windows boots
- **Auto-load layout on startup** - Load your saved layout automatically

### System Tray

- **Close Window (X)** - Minimizes to system tray (doesn't exit)
- **Tray Icon** - Right-click for menu options:
  - Show Controller
  - Hide Controller
  - Exit (fully close the app)
- **Double-click tray icon** - Show the controller window

## Configuration Files

Settings are stored in:
```
C:\Users\YourUsername\AppData\Roaming\DesktopOverlay\
├── overlay_config.json    (saved layouts)
└── overlay_settings.json  (app settings)
```

## Building from Source

To create your own executable:

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name "DesktopOverlay" overlay.py --icon=Ameno.ico --add-data "Ameno.ico;."
```

The executable will be in the `dist` folder.

## Keyboard Shortcuts

| Action | Shortcut |
|--------|----------|
| Resize | Left Click + Scroll |
| Rotate | Right Click + Scroll |
| Move | Click & Drag |

## Tips & Tricks

- Use **click-through mode** to keep overlays visible while working without blocking clicks
- Lower **opacity** for subtle reference images that don't obstruct your view
- **Save layouts** for different workflows (coding, gaming, art, etc.)
- Use **z-order** control to layer multiple overlays perfectly
- Enable **auto-start** and **auto-load** for a seamless experience

## Troubleshooting

**Overlay won't move/resize:**
- Make sure "Click-through mode" is unchecked

**App opens multiple times on startup:**
- Uncheck "Run at Windows startup", restart, then check it again

**Can't find saved layouts:**
- Check `%APPDATA%\DesktopOverlay\` folder

**Overlays disappear after restart:**
- Make sure you clicked "Save Layout" before closing
- Enable "Auto-load layout on startup"

## Requirements

- Windows 10/11
- Python 3.7+ (if running from source)
- PyQt5 (if running from source)

## License

[MIT License](LICENSE)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Credits

Created by [Ameno](https://github.com/AmenoHoshizora)

## Support

If you encounter any issues or have suggestions, please [open an issue](../../issues).

---

⭐ If you find this project useful, please consider giving it a star!
