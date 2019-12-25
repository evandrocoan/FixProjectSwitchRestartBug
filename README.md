# Fix Project Switch Restart Bug


Fix some Sublime Text sections issues as does not set the last scroll position after a project change.
1. [SublimeTextIssues#1379](https://github.com/SublimeTextIssues/Core/issues/1379) Restore session, does not set the last scroll position after a project change, or sublime restart
1. [BufferScroll#23](https://github.com/titoBouzout/BufferScroll/issues/23) Scroll sync doesn't work (ST3 3084)
1. [SublimeTextStudio#26](https://github.com/evandrocoan/SublimeTextStudio/issues/26) Finish the package: Fix Project Switch-Restart Bug

See:
1. [Main.sublime-menu](Main.sublime-menu)
1. [Default.sublime-commands](Default.sublime-commands)
1. [Preferences.sublime-settings](Preferences.sublime-settings)

Need to fix to the bug on the Sublime Text core, where all cloned views are called with the same
view object. If we do not fix this here, it would set all the cloned views to the same
position. So to overcome this, we call all the views to center with `plugin_loaded()`.

#1253 Event handlers for cloned views get called with the wrong view object
https://github.com/SublimeTextIssues/Core/issues/1253

The `on_load_async()` is called for each view on for the project change, however
due the bug https://github.com/SublimeTextIssues/Core/issues/1253, the cloned
views are called with the wrong `view`, then we need to call `plugin_loaded()` to catch
all the correct views (including the cloned ones) to apply the scroll fix for the bug
https://github.com/SublimeTextIssues/Core/issues/1379.


## Installation

### By Package Control

1. Download & Install **`Sublime Text 3`** (https://www.sublimetext.com/3)
1. Go to the menu **`Tools -> Install Package Control`**, then,
   wait few seconds until the installation finishes up
1. Now,
   Go to the menu **`Preferences -> Package Control`**
1. Type **`Add Channel`** on the opened quick panel and press <kbd>Enter</kbd>
1. Then,
   input the following address and press <kbd>Enter</kbd>
   ```
   https://raw.githubusercontent.com/evandrocoan/StudioChannel/master/channel.json
   ```
1. Go to the menu **`Tools -> Command Palette...
   (Ctrl+Shift+P)`**
1. Type **`Preferences:
   Package Control Settings – User`** on the opened quick panel and press <kbd>Enter</kbd>
1. Then,
   find the following setting on your **`Package Control.sublime-settings`** file:
   ```js
       "channels":
       [
           "https://packagecontrol.io/channel_v3.json",
           "https://raw.githubusercontent.com/evandrocoan/StudioChannel/master/channel.json",
       ],
   ```
1. And,
   change it to the following, i.e.,
   put the **`https://raw.githubusercontent...`** line as first:
   ```js
       "channels":
       [
           "https://raw.githubusercontent.com/evandrocoan/StudioChannel/master/channel.json",
           "https://packagecontrol.io/channel_v3.json",
       ],
   ```
   * The **`https://raw.githubusercontent...`** line must to be added before the **`https://packagecontrol.io...`** one, otherwise,
     you will not install this forked version of the package,
     but the original available on the Package Control default channel **`https://packagecontrol.io...`**
1. Now,
   go to the menu **`Preferences -> Package Control`**
1. Type **`Install Package`** on the opened quick panel and press <kbd>Enter</kbd>
1. Then,
search for **`FixProjectSwitchRestartBug`** and press <kbd>Enter</kbd>

See also:

1. [ITE - Integrated Toolset Environment](https://github.com/evandrocoan/ITE)
1. [Package control docs](https://packagecontrol.io/docs/usage) for details.


___
## License

All files in this repository are released under GNU General Public License v3.0
or the latest version available on http://www.gnu.org/licenses/gpl.html

1. The [LICENSE](LICENSE) file for the GPL v3.0 license
1. The website https://www.gnu.org/licenses/gpl-3.0.en.html

For more information.


