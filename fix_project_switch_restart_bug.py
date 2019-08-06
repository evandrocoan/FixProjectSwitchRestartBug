


import sublime
import sublime_plugin

import time

MAXIMUM_CYCLES = 50

isCurrentlySwitching = False
last_focused_goto_definition = False


class ForceRestoringViewsScrollingCommand( sublime_plugin.TextCommand ):

    def run( self, edit ):
        fix_all_views_scroll()
        sublime.set_timeout( fix_all_views_scroll2, 2000 )



def fix_all_views_scroll():
    global isCurrentlySwitching

    if not isCurrentlySwitching:
        isCurrentlySwitching = True
        __windows            = sublime.windows()[:MAXIMUM_CYCLES]

        windows      = []
        activeViews  = []
        windowsViews = []

        for window in __windows:
            windows.append( window )
            activeViews.append( window.active_view() )
            windowsViews.append( window.views()[:MAXIMUM_CYCLES] )

        def revealWindow():
            global isCurrentlySwitching

            if( len( windowsViews ) > 0 ):

                if( len( windowsViews[-1] ) > 0 ):
                    revealView( windows[-1], windowsViews[-1].pop() )
                    sublime.set_timeout( revealWindow, 100 );

                else:
                    # Restore the original active view.
                    view   = activeViews.pop()
                    window = windows.pop()

                    # Allow new switching fixes.
                    isCurrentlySwitching = False
                    windowsViews.pop()

                    while view.is_loading():
                        time.sleep(0.2)

                    revealView( window, view )

        sublime.set_timeout( revealWindow, 200 )



def fix_all_views_scroll2():
    views         = None
    windows       = sublime.windows()[:MAXIMUM_CYCLES]
    # currentViewId = 0

    for window in windows:
        views         = window.views()[:MAXIMUM_CYCLES]
        # currentViewId = window.active_view().id()

        for view in views:
            # print( "( fix_all_views_scroll2 ) View id {0}, buffer id {1}".format( view.id(), view.buffer_id() ) )
            # if currentViewId != view.id():

            while view.is_loading():
                time.sleep(0.2)

            restore_view( view )


def revealView( window, view ):
    window.focus_view( view )
    restore_view( view )


def plugin_loaded():
    # print( "( plugin_loaded ) fix_project_switch_restart_bug.py" )

    sublime.set_timeout( fix_all_views_scroll, 1000 )
    sublime.set_timeout( fix_all_views_scroll2, 5000 )


def restore_view( view ):
    """
        view.set_viewport_position( , False )
    """
    # for selection in view.sel(): print( "( fix_project_switch_restart_bug.py ) Iterating view.sel()[i].begin() {0}".format( selection ) )

    # print( "( fix_project_switch_restart_bug.py ) Setting show_at_center to view id {0}".format( view.id() ) )
    # view.run_command( "move", {"by": "lines", "forward": False} )
    # view.run_command( "move", {"by": "lines", "forward": True} )
    try:
        view.show_at_center( view.sel()[0].begin() )

    except Exception:
        pass



def are_we_on_the_project_switch_process():
    """
        Call `plugin_loaded()` only one time, after the project switch process is finished.

        Restrictions:
            1. We cannot call `plugin_loaded()` if this function is called only one time.
            2. If this function is called consequently 2 times with less than 0.1 seconds, then we
               must to return True.
    """
    # Fix SyntaxWarning: name 'last_focused_goto_definition' is used prior to global declaration
    global last_focused_goto_definition

    # If we are on the seconds of listening period after the command `prompt_select_workspace`
    # being run, we know we probably switching projects. Therefore, schedules the project fix.
    if last_focused_goto_definition:
        last_focused_goto_definition = False
        run_delayed_fix()

    return False



def run_delayed_fix():
    sublime.set_timeout( fix_all_views_scrollSwitch, 2000 )
    sublime.set_timeout( fix_all_views_scrollSwitch2, 5000 )



class OnLoadedViewCommand( sublime_plugin.EventListener ):

    # def on_load( self, view ):
    def on_load_async( self, view ):
    # def on_activated( self, view ):
    # def on_activated_async( self, view ):

        # { "keys": ["up"], "command": "move", "args": {"by": "lines", "forward": false} },
        # { "keys": ["down"], "command": "move", "args": {"by": "lines", "forward": true} },
        # view.run_command( "move", {"by": "lines", "forward": False} )
        # view.run_command( "move", {"by": "lines", "forward": True} )
        #
        # print( "( fix_project_switch_restart_bug.py ) Calling restore_view, view id {0}".format( view.id() ) )
        if not are_we_on_the_project_switch_process():
            restore_view( view )



isCurrentlySwitchingSwitch = False

def fix_all_views_scrollSwitch():
    global isCurrentlySwitchingSwitch

    if not isCurrentlySwitchingSwitch:
        isCurrentlySwitchingSwitch = True
        __window                   = sublime.active_window()

        windowsViews  = []
        activeViews   = []
        activeWindows = []

        activeWindows.append( __window )
        activeViews.append( __window.active_view() )
        windowsViews.append( __window.views()[:MAXIMUM_CYCLES] )

        def revealWindow():

            global isCurrentlySwitchingSwitch

            if( len( windowsViews ) > 0 ):

                if( len( windowsViews[-1] ) > 0 ):

                    revealView( activeWindows[-1], windowsViews[-1].pop() )
                    sublime.set_timeout( revealWindow, 100 );

                else:

                    # Restore the original active view.
                    view   = activeViews.pop()
                    window = activeWindows.pop()

                    # Allow new switching fixes.
                    isCurrentlySwitchingSwitch = False

                    windowsViews.pop()
                    revealView( window, view )

        sublime.set_timeout( revealWindow, 200 )



def fix_all_views_scrollSwitch2():

    views         = None
    windows       = sublime.windows()[:MAXIMUM_CYCLES]
    # currentViewId = 0

    views         = sublime.active_window().views()[:MAXIMUM_CYCLES]
    # currentViewId = window.active_view().id()

    for view in views:
        # print( "( fix_all_views_scroll2 ) View id {0}, buffer id {1}".format( view.id(), view.buffer_id() ) )
        # if currentViewId != view.id():
        restore_view( view )



def unlockTheScrollRestoring():
    global last_focused_goto_definition
    last_focused_goto_definition = False


class SampleListener( sublime_plugin.EventListener ):

    def on_window_command( self, window, command, args ):

        # print( "About to execute " + command )

        if command == "open_recent_project_or_workspace":
            # print( "On " + command )
            run_delayed_fix()

        elif command == "prompt_select_workspace":
            global last_focused_goto_definition
            last_focused_goto_definition = True

            sublime.set_timeout( unlockTheScrollRestoring, 10000 )





