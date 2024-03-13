from kivy.clock import Clock , mainthread
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import Screen , ScreenManager
from kivy.properties import ListProperty, ObjectProperty , BooleanProperty , StringProperty , DictProperty , NumericProperty
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.animation import Animation

from datetime import datetime

# ------------------------ Guest Screens ----------------------
class LocationImageContainer(BoxLayout) :
    locationName: Label = ObjectProperty()
    locationImage: Image = ObjectProperty()


class LocationInformationContainer(BoxLayout) :
    title: Label = ObjectProperty()
    info: Label = ObjectProperty()


class LocationScreenInformation(Screen) :
    enter_animate = Animation(opacity=1, duration=0.5)
    leave_animate = Animation(opacity=0, duration=0.5)

    image1: LocationImageContainer = ObjectProperty()
    image2: LocationImageContainer = ObjectProperty()
    directions: LocationInformationContainer = ObjectProperty()
    information: LocationInformationContainer = ObjectProperty()

    __data: dict = ObjectProperty(None)
    isRoom: bool = BooleanProperty(True)
    screen_id: str = StringProperty("")

    ifNoTimeSpecifiedUseThisKey = "office"
    time_parser = datetime.strptime
    time_format = "%H:%M:%S"
    time_split_letter = "-"
    time_day_splitter = "/"
    teacher_time: list[[str, datetime, datetime], ...] = ListProperty([])

    # Data Structure teacher_time : [ (room, time_start , time_end, day ) , ]

    def on_kv_post(self, base_widget) :
        self.information.title.text = "INFORMATION"
        self.information.info.text = "    This room is an inventory room for all the un used supply"

    def on_enter(self, *args) :
        self.enter_animate.start(self)
        self.updateOnlyTeacherScreen()

    def on_leave(self, *args) :
        self.leave_animate.start(self)

    def getScreenInformation(self) -> dict :
        # Data Structure = { directions : ( text , int ) }
        if self.isRoom :
            return {"directions" : self.__data["directions"]}
        else :
            return {"directions" : [self.directions.info.text, 9]}

    def updateOnlyTeacherScreen(self) :
        # TODO: Update the screen if it TEACHER Screen
        current_time = datetime.now()
        if self.parent and self.screen_id and not self.isRoom :
            for name, time_start, time_end, day in self.teacher_time :
                if current_time.weekday() == day: # Check if the current day is the saved day
                    if time_start.hour <= current_time.hour <= time_end.hour :  # Check if the current hour in the hour range
                        if time_start.minute <= current_time.minute :  # Check if the current minute in the minute range
                            # TODO: Set new location screen for teacher
                            room_data = self.parent.parent.parent.parent.getSpecificRoom(name)
                            self.image2.locationImage.source = room_data["building picture"]
                            self.image2.locationName.text = room_data["name"]
                            self.directions.info.text = room_data["directions"][0]
                        break
            else :
                # TODO: Set new location screen for teacher if no specified room
                room_data = self.parent.parent.parent.parent.getSpecificRoom(self.ifNoTimeSpecifiedUseThisKey)
                self.image2.locationImage.source = room_data["building picture"]
                self.image2.locationName.text = room_data["name"]
                self.directions.info.text = room_data["directions"][0]

    def updateScreen(self, data: dict, isRoom: bool, key: str) :
        self.__data = data
        self.isRoom = isRoom
        self.screen_id = key
        if isRoom :
            # TODO: Display the needed data for rooms
            self.image1.locationName.text = data["name"]
            self.image1.locationImage.source = data["building picture"]
            self.image2.locationName.text = data["floor"]
            self.image2.locationImage.source = data["floor picture"]
            self.information.info.text = data["brief information"][0]
            self.directions.info.text = data["directions"][0]
        else :
            # TODO: Display the needed data for teacher
            self.image1.locationName.text = data["person"]
            self.image1.locationImage.source = data["picture"]
            self.information.info.text = data["information"]
            for location, overall_time in data["locations"].items() :
                for time_in_room in overall_time :
                    time_in_room, day = time_in_room.split(self.time_day_splitter)
                    time_start, time_end = time_in_room.split(self.time_split_letter)
                    time_start = self.time_parser(time_start, self.time_format)
                    time_end = self.time_parser(time_end, self.time_format)
                    self.teacher_time.append((location, time_start, time_end , int(day)))


class GuestScreen(Screen) :
    screens_handler: ScreenManager = ObjectProperty(None)
    preview_screens_names: list = ListProperty(["screen_1" , "screen_2"])

    screens_names : list[str , ...] = ListProperty([]) # list [ screen_name ]
    screens_data : dict = DictProperty({})
    is_screen_is_room : dict = DictProperty({}) # screen_name = bool

    __okey_to_animate = True
    __changing_speed = 15

    index_of_screen : int = NumericProperty(0) # Represent What Screen to display
    index_of_content_screen : int = NumericProperty(0) # Represent What content to show
    main_event : Clock = None
    changing_screen_event : Clock = None

    def update_activity(self, interval: float) :
        if self.parent :
            if self.parent.parent.location_selected :
                self.changeScreen(self.parent.parent.location_selected)
                self.parent.parent.location_selected = ""

    def changeScreen(self, name: str) :
        if name not in self.screens_names :
            raise Exception(f"Can't change screen, {name} screen does not exist")
        self.__okey_to_animate = False
        preview_screen = self.preview_screens_names[0] if self.screens_handler.current == self.preview_screens_names[1] else self.preview_screens_names[1]
        hidden_screen: LocationScreenInformation = self.screens_handler.get_screen(preview_screen)
        data = self.screens_data[name]
        isRoom = self.is_screen_is_room[name]
        hidden_screen.updateScreen(data=data, isRoom=isRoom, key=name)
        self.screens_handler.current = preview_screen

    def okeyToChangeScreen(self) :
        if not self.__okey_to_animate:
            self.__okey_to_animate = True

    def loadScreen(self, *args):
        self.main_event = Clock.schedule_interval(self.update_activity, 1 / 30)
        if self.parent :

            self.parent.parent.loadScreenData()

            # Nag Save san parent data
            for instructor , info in self.parent.parent.getInstructorData().items():
                self.screens_data[instructor] = info
                self.screens_names.append( instructor )
                self.is_screen_is_room[instructor] = False

            for room , info in self.parent.parent.getRoomData().items():
                self.screens_data[room] = info
                self.screens_names.append( room )
                self.is_screen_is_room[room] = True

        # Duwa lang na screens tas binutangan ko san data dayon an una na screen
        fist_screen = LocationScreenInformation(name = self.preview_screens_names[0])
        fist_screen.updateScreen(data=self.screens_data[self.screens_names[0]] , isRoom=self.is_screen_is_room[self.screens_names[0]], key=self.screens_names[0] )
        self.screens_handler.add_widget(fist_screen)
        self.screens_handler.add_widget(LocationScreenInformation(name=self.preview_screens_names[1]))

        self.animateChangingScreens()

    def on_enter(self, *args) :
        Clock.schedule_once(self.loadScreen)

    @mainthread
    def animate(self , *args):
        self.index_of_screen = self.index_of_screen + 1 if (self.index_of_screen + 1) < len(self.preview_screens_names) else 0
        self.index_of_content_screen = self.index_of_content_screen + 1 if ( self.index_of_content_screen + 1 ) < len(self.screens_names ) else 0

        hidden_screen_name = self.preview_screens_names[self.index_of_screen]
        hidden_screen : LocationScreenInformation = self.screens_handler.get_screen(hidden_screen_name)
        hidden_screen.updateScreen(data=self.screens_data[self.screens_names[self.index_of_content_screen]] ,
                                   isRoom=self.is_screen_is_room[self.screens_names[self.index_of_content_screen]],
                                   key=self.screens_names[self.index_of_content_screen])

        self.screens_handler.current = self.preview_screens_names[self.index_of_screen]
        self.changing_screen_event = Clock.schedule_once(self.animateChangingScreens , self.__changing_speed)

    def animateChangingScreens(self , *args) :
        if self.__okey_to_animate :
            self.changing_screen_event = Clock.schedule_once(self.animate, self.__changing_speed)
        else :
            self.changing_screen_event = Clock.schedule_once(self.animateChangingScreens , 1 )

    def controlVariables(self, okey_to_animate=None, changing_speed=None) :
        if okey_to_animate is not None :
            self.__okey_to_animate = okey_to_animate
        if changing_speed is not None :
            self.__changing_speed = changing_speed

    def on_leave(self, *args):
        self.__okey_to_animate = False
        Clock.unschedule(self.main_event)
        Clock.unschedule(self.changing_screen_event)

    def getDataFromKey(self , name : str) -> dict:
        if self.is_screen_is_room.get(name) :
            return self.screens_data[name]
        else:
            return self.screens_handler.current_screen.getScreenInformation()
