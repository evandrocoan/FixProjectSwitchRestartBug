import sublime
import sublime_plugin

import threading
import time

MAXIMUM_CYCLES = 50

TIME_AFTER_FOCUS_VIEW = 30
TIME_AFTER_FOCUS_GROUP = 250

TIME_AFTER_RESTORE_VIEW = 15
TIME_AFTER_START_RUNNING = 2000

enable_project_switch_event_listener = (
    "prompt_select_workspace",
    "prompt_switch_project_or_workspace",
    "prompt_open_project_or_workspace",
)


try:
    # Do not import State directly to not break us in case the MaxPane.max_pane module is reloaded
    import MaxPane

except ImportError as error:
    print('FixProjectSwitchRestartBug Error: Could not import the MaxPane package!', error)

    class MaxPane(object):

        class max_pane(object):

            class State(object):
                disable_timeout = False


# https://stackoverflow.com/questions/128573/using-property-on-classmethods
class StateMeta(type):

    def __init__(cls, *args, **kwargs):
        cls.last_on_load_time = None

        cls._is_currently_switching = False
        cls._has_opened_the_project_switch_panel = False

    @property
    def is_currently_switching(cls):
        return cls._is_currently_switching

    @is_currently_switching.setter
    def is_currently_switching(cls, value):
        cls._is_currently_switching = value
        MaxPane.max_pane.State.disable_timeout = value

    @property
    def has_opened_the_project_switch_panel(cls):
        return cls._has_opened_the_project_switch_panel

    @has_opened_the_project_switch_panel.setter
    def has_opened_the_project_switch_panel(cls, value):
        cls.last_on_load_time = None
        cls._has_opened_the_project_switch_panel = value


# I am saving the state in this class because it is a royal pain in the ass
# to keep typing `global` every time/everywhere I would like to use a global!
class State(metaclass=StateMeta):
    fixed_views = []
    has_opened_the_project_switch_panel = False


class ForceRestoringViewsScrollingCommand(sublime_plugin.TextCommand):

    def run(self, edit, active_window_only, source_event):

        if State.is_currently_switching:
            print( "Already fixing all views scrolling... active_window_only", active_window_only, "source_event", source_event )

        else:
            print( "Fixing all views scrolling... active_window_only", active_window_only, "source_event", source_event )
            State.is_currently_switching = True
            sublime.set_timeout( lambda: fix_all_views_scroll( active_window_only ), TIME_AFTER_START_RUNNING )


def set_read_only(window, views):
    """ Avoid us accidentally changing the buffer when scrolling around """
    fixed_views = []
    active_views = {}

    for view in views:
        view_group = window.get_view_index( view )
        is_read_only = view.is_read_only()

        if not is_read_only:
            view.set_read_only( True )

        if view_group != -1:
            view_group, index = view_group

            if view_group not in active_views:
                active_view_in_group = window.active_view_in_group( view_group )
                active_views[view_group] = active_view_in_group

            fixed_views.append( (view, view_group, is_read_only ) )

    # print( "%s" % "\n".join( "group %s: view %s index %s '%s'" % ( group + 1, view.id(), window.get_view_index( view )[1], view.file_name() if view.file_name() else repr( view.substr( sublime.Region( 0, 100 ) ) ) ) for group, view in active_views.items() ) )
    return list( sorted( fixed_views, key=lambda item: item[1] ) ), active_views


def fix_all_views_scroll(active_window_only):
    generator = view_generator( active_window_only )

    def recursive_reveal():

        try:
            view, group, window, end_of_group, start_of_group, active_view = next( generator )
            # print( "Fixing   window %s group %s view %s %s" % ( window.id(), group + 1, view.id(), repr( view.file_name() if view.file_name() else view.substr( sublime.Region( 0, 100 ) ) ) ) )

            if start_of_group:
                def do_start_of_group():
                    window.focus_view( view )

                    if end_of_group:
                        next_target = lambda: fix_all_views_scroll_hidden( window, group, recursive_reveal )
                        sublime.set_timeout( lambda: restore_view( view, window, next_target ), TIME_AFTER_FOCUS_VIEW )
                    else:
                        sublime.set_timeout( lambda: restore_view( view, window, recursive_reveal ), TIME_AFTER_FOCUS_VIEW )

                window.focus_group( group )
                sublime.set_timeout( do_start_of_group, TIME_AFTER_FOCUS_GROUP )

            elif end_of_group:
                def focus_active_view():
                    window.focus_view( active_view )

                    next_target = lambda: fix_all_views_scroll_hidden( window, group, recursive_reveal )
                    sublime.set_timeout( lambda: restore_view( active_view, window, next_target ), TIME_AFTER_FOCUS_VIEW )

                window.focus_view( view )
                sublime.set_timeout( lambda: restore_view( view, window, focus_active_view ), TIME_AFTER_FOCUS_VIEW )

            else:
                window.focus_view( view )
                sublime.set_timeout( lambda: restore_view( view, window, recursive_reveal ), TIME_AFTER_FOCUS_VIEW )

        except StopIteration:
            State.is_currently_switching = False

            # print( "Finished restoring focus..." )
            for view, group, is_read_only in State.fixed_views:

                if not is_read_only:
                    view.set_read_only( False )

    recursive_reveal()


def view_generator(active_window_only):
    windows = [ sublime.active_window() ] if active_window_only else sublime.windows()[:MAXIMUM_CYCLES]

    for window in windows:
        active_group = window.active_group()
        views = window.views()[:MAXIMUM_CYCLES]

        State.fixed_views, active_views = set_read_only( window, views )
        last_group = None

        for index, values in enumerate( State.fixed_views ):
            index += 1
            view, group, _ = values
            active_view = active_views[group]

            if index < len( State.fixed_views ):
                _, next_group, _ = State.fixed_views[index]

            else:
                next_group = group + 1

            end_of_group = group != next_group
            start_of_group = group != last_group

            last_group = group
            yield view, group, window, end_of_group, start_of_group, active_view

        for view, group, is_read_only in State.fixed_views:

            if not is_read_only:
                view.set_read_only( False )

        window.focus_group( active_group )


def restore_view(view, window, next_target, withfocus=True):

    if view.is_loading():
        sublime.set_timeout( lambda: restore_view( view, window, next_target, withfocus=withfocus ), 200 )

    else:
        selections = view.sel()
        file_name = view.file_name()

        if len( selections ):
            first_selection = selections[0].begin()
            original_selections = list( selections )

            def super_refocus():
                view.run_command( "move", {"by": "lines", "forward": False} )
                view.run_command( "move", {"by": "lines", "forward": True} )

                def fix_selections():
                    selections.clear()

                    for selection in original_selections:
                        selections.add( selection )

                    sublime.set_timeout( next_target, TIME_AFTER_RESTORE_VIEW )

                sublime.set_timeout( fix_selections, TIME_AFTER_RESTORE_VIEW )

            if file_name and withfocus:

                def reforce_focus():
                    # https://github.com/SublimeTextIssues/Core/issues/1482
                    group, view_index = window.get_view_index( view )
                    window.set_view_index( view, group, 0 )

                    # https://github.com/SublimeTextIssues/Core/issues/538
                    row, column = view.rowcol( first_selection )
                    window.open_file( "%s:%d:%d" % ( file_name, row + 1, column + 1 ), sublime.ENCODED_POSITION )
                    window.set_view_index( view, group, view_index )

                    # print( 'Super reforce focus focusing...' )
                    sublime.set_timeout( super_refocus, TIME_AFTER_RESTORE_VIEW )

                view.show_at_center( first_selection )
                sublime.set_timeout( reforce_focus, TIME_AFTER_FOCUS_VIEW )

            else:
                view.show_at_center( first_selection )
                sublime.set_timeout( super_refocus, TIME_AFTER_RESTORE_VIEW )


def fix_all_views_scroll_hidden(window, group, next_target):
    generator = view_generator_hidden(window, group)

    def recursive_reveal():
        try:
            view, window = next( generator )

            file_name = view.file_name()
            if not file_name: file_name = view.substr( sublime.Region( 0, 100 ) )

            # print( "Refixing window %s group %s view %s %s" % ( window.id(), group + 1, view.id(), repr( file_name ) ) )
            restore_view( view, window, recursive_reveal, withfocus=False )

        except StopIteration:
            sublime.set_timeout( next_target, TIME_AFTER_RESTORE_VIEW )

    # No timeout out here because no action was performed by us yet and whoever called us, already set a timeout
    # sublime.set_timeout( recursive_reveal )
    sublime.set_timeout( next_target )


def view_generator_hidden(window, group):
    views = window.views_in_group( group )[:MAXIMUM_CYCLES]

    for view in views:
        yield view, window


def run_delayed_fix(active_window_only, window, source_event):
    window.run_command(
            'force_restoring_views_scrolling', {
                'active_window_only': active_window_only,
                'source_event': source_event,
            }
        )


def plugin_loaded():
    pass
    run_delayed_fix( False, sublime.active_window(), 'plugin_loaded' )


def unlockTheScrollRestoring():
    State.has_opened_the_project_switch_panel = False


class SampleListener( sublime_plugin.EventListener ):

    def on_load( self, view ):
        # print( "on_load", view.file_name() if view.file_name() else repr( view.substr( sublime.Region( 0, 100 ) ) ) )

        if State.has_opened_the_project_switch_panel:
            load_time = time.time()
            last_on_load_time = State.last_on_load_time

            if last_on_load_time and load_time - last_on_load_time < 0.5:
                State.has_opened_the_project_switch_panel = False

                window = view.window() or sublime.active_window()
                run_delayed_fix( True, window, 'on_load' )

            else:
                State.last_on_load_time = time.time()

    def on_window_command( self, window, command, args ):
        # print( "command", command, args )

        if command == "open_recent_project_or_workspace":
            run_delayed_fix( True, window, 'open_recent_project_or_workspace' )

        elif command in enable_project_switch_event_listener:
            State.has_opened_the_project_switch_panel = True
            sublime.set_timeout( unlockTheScrollRestoring, 60000 )

