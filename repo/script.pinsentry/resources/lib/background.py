import xbmcaddon
import xbmcgui

# Import the common settings
from resources.lib.settings import log
from resources.lib.settings import Settings

ADDON = xbmcaddon.Addon(id='script.pinsentry')
CWD = ADDON.getAddonInfo('path')


# Class to set the background while a pin is prompted for
class Background(xbmcgui.WindowXML):
    BACKGROUND_IMAGE_ID = 3004

    @staticmethod
    def createBackground():
        # Check to see if the background is enabled
        if not Settings.isDisplayBackground():
            return None
        return Background("pinsentry-background.xml", CWD)

    def onInit(self):
        xbmcgui.WindowXML.onInit(self)

        # Get the background image to be used
        bgImage = Settings.getBackgroundImage()

        if bgImage is not None:
            log("Background: Setting background image to %s" % bgImage)
            bgImageCtrl = self.getControl(Background.BACKGROUND_IMAGE_ID)
            bgImageCtrl.setImage(bgImage)
