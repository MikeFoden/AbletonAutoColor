import Live
from ableton.v2.control_surface import ControlSurface
from functools import partial

# Dictionary of track names and their corresponding color indices
track_colors = {
    "ki": 0, # kicks - red
    "dr": 1, # drums - orange
    "ha": 1, # hats - orange
    "cl": 1, # claps - orange
    "sn": 2, # snares - orange
    "ba": 8, # bass - blue
    "le": 5, # leads - green
    "sy": 6, # synths - grass green
    "pl": 4, # plucks - lighter green
    "vo": 3, # vocals - yellow
    "pa": 12, # pads - pink
    "am": 12, # ambience - pink
    "fx": 13, # fx - white
    "si": 69 # sidechain - black 
}

def assign_track_color(track):
    """Assigns a color to a track based on its name"""
    track_name = track.name
    temp_name = track_name.lower()[0:2]
    if temp_name in track_colors:
        color_index = track_colors[temp_name]
        track.color_index = color_index

def get_all_tracks(doc):
    all_tracks = []
    for track in doc.tracks:
        all_tracks.append(track)
        if hasattr(track, 'is_foldable') and track.is_foldable:
            all_tracks.extend(get_nested_tracks(track))
    return all_tracks

def get_nested_tracks(group_track):
    nested_tracks = []
    for track in group_track.canonical_parent.tracks:
        if hasattr(track, 'is_grouped') and track.is_grouped and track.group_track == group_track:
            nested_tracks.append(track)
            if hasattr(track, 'is_foldable') and track.is_foldable:
                nested_tracks.extend(get_nested_tracks(track))
    return nested_tracks

class ColorChanger(ControlSurface):
    def __init__(self, c_instance):
        ControlSurface.__init__(self, c_instance)
        app = Live.Application.get_application()
        self.doc = app.get_document()
        self.previous_track_ids = set(track._live_ptr for track in get_all_tracks(self.doc))
        # Assign colors to existing tracks on initialization
        self.assign_colors_to_existing_tracks()
        # Register the listener functions
        self.doc.add_tracks_listener(self.tracks_changed_listener)

        for track in get_all_tracks(self.doc):
            track.add_name_listener(partial(self.track_name_changed_listener, track))

    def tracks_changed_listener(self):
        """Listener function called when a track is added or deleted"""
        current_track_ids = set(track._live_ptr for track in self.doc.tracks)
        self.schedule_message(0, lambda: self.handle_track_change(current_track_ids))

    def handle_track_change(self, current_track_ids):
        new_track_id = current_track_ids - self.previous_track_ids
        deleted_track_id = self.previous_track_ids - current_track_ids

        if new_track_id:
            new_track_id = new_track_id.pop()
            new_track = None
            for track in self.doc.tracks:
                if track._live_ptr == new_track_id:
                    new_track = track
                    break
            if new_track is not None:
                assign_track_color(new_track)
                # Attach the event listener to the new track
                new_track.add_name_listener(lambda: self.track_name_changed_listener(new_track))

        self.previous_track_ids = current_track_ids

    def assign_colors_to_existing_tracks(self):
        """Assigns colors to existing tracks based on their names"""
        for track in self.doc.tracks:
            assign_track_color(track)

    def track_name_changed_listener(self, track):
        """Listener function called when a track's name is changed"""
        self.schedule_message(0, lambda: assign_track_color(track))
