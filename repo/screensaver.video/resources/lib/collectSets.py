# -*- coding: utf-8 -*-
import traceback
import base64
import xml.etree.ElementTree as ET
import xbmc
import xbmcaddon
import xbmcvfs
import xbmcgui

# Import the common settings
from resources.lib.settings import log
from resources.lib.settings import Settings
from resources.lib.settings import os_path_join
from resources.lib.settings import os_path_split

ADDON = xbmcaddon.Addon(id='screensaver.video')
ICON = ADDON.getAddonInfo('icon')


class CollectSets():
    def __init__(self):
        addonRootDir = xbmcvfs.translatePath('special://profile/addon_data/%s' % ADDON.getAddonInfo('id'))
        self.collectSetsFile = os_path_join(addonRootDir, 'collectsets.xml')
        self.disabledVideosFile = os_path_join(addonRootDir, 'disabled.xml')

    def getCollections(self):
        collectionMap = {}
        # Add the default set of collections
        ## deleted default collections as they are now longer online available

        # Now add any custom collections
        customCollections = self.getCustomCollectionSets()
        collectionMap.update(customCollections)

        return collectionMap

    def loadCollection(self, collectionFile, removeDisabled=True):
        log("CollectSets: Loading collection %s" % collectionFile)
        if not xbmcvfs.exists(collectionFile):
            log("CollectSets: Failed to load collection file: %s" % collectionFile, xbmc.LOGERROR)
            return None

        # Load all of the videos that are disabled
        disabledVideos = []
        if removeDisabled:
            disabledVideos = self.getDisabledVideos()

        collectionDetails = None
        try:
            # Load the file as a string
            collectionFileRef = xbmcvfs.File(collectionFile, 'r')
            collectionStr = collectionFileRef.read()
            collectionFileRef.close()

            collectionElem = ET.ElementTree(ET.fromstring(collectionStr))

            collectionName = collectionElem.find('collection')
            if collectionName in [None, ""]:
                return None

            collectionDetails = {'name': None, 'image': None, 'videos': []}
            collectionDetails['name'] = collectionName.text

            log("CollectSets: Collection Name is %s" % collectionDetails['name'])

            # Record which sets are builtin to the addon
            collectionDetails['builtin'] = 'false'
            builtinElem = collectionElem.getroot().find('builtin')
            if builtinElem not in [None, ""]:
                if builtinElem.text == 'true':
                    collectionDetails['builtin'] = 'true'

            isEncoded = False
            encodedElem = collectionElem.getroot().find('encoded')
            if encodedElem not in [None, ""]:
                if encodedElem.text == 'true':
                    isEncoded = True

            imageElem = collectionElem.getroot().find('image')
            if imageElem not in [None, ""]:
                collectionDetails['image'] = imageElem.text

            # Get the videos that are in the collection
            for elemItem in collectionElem.findall('video'):
                video = {'name': None, 'filename': None, 'image': ICON, 'duration': None, 'primary': None, 'enabled': True}

                nameElem = elemItem.find('name')
                if nameElem not in [None, ""]:
                    video['name'] = nameElem.text

                filenameElem = elemItem.find('filename')
                if filenameElem not in [None, ""]:
                    video['filename'] = filenameElem.text

                imageElem = elemItem.find('image')
                if imageElem not in [None, ""]:
                    video['image'] = imageElem.text

                durationElem = elemItem.find('duration')
                if durationElem not in [None, "", 0]:
                    if durationElem.text not in [None, "", 0]:
                        video['duration'] = int(durationElem.text)

                primaryElem = elemItem.find('primary')
                if nameElem not in [None, ""]:
                    if isEncoded:
                        video['primary'] = base64.b64decode(primaryElem.text)
                    else:
                        video['primary'] = primaryElem.text

                # Check if this video is in the disabled list
                if video['filename'] in disabledVideos:
                    video['enabled'] = False

                collectionDetails['videos'].append(video)
        except:
            log("CollectSets: Failed to read collection file %s" % collectionFile, xbmc.LOGERROR)
            log("CollectSets: %s" % traceback.format_exc(), xbmc.LOGERROR)

        return collectionDetails

    # Gets the files that have been recorded as disabled
    def getDisabledVideos(self):
        disabledVideos = []
        # Check if the disabled videos file exists
        if not xbmcvfs.exists(self.disabledVideosFile):
            log("CollectSets: No disabled videos file exists")
            return disabledVideos

        try:
            # Load the file as a string
            disabledVideosFileRef = xbmcvfs.File(self.disabledVideosFile, 'r')
            disabledVideosStr = disabledVideosFileRef.read()
            disabledVideosFileRef.close()

            disabledVideosElem = ET.ElementTree(ET.fromstring(disabledVideosStr))

            # Expected XML format:
            # <disabled_screensaver>
            #     <filename></filename>
            # </disabled_screensaver>

            # Get the videos that are in the disabled list
            for filenameItem in disabledVideosElem.getroot().findall('filename'):
                disabledFile = filenameItem.text

                log("CollectSets: Disabled video file: %s" % disabledFile)
                disabledVideos.append(disabledFile)
        except:
            log("CollectSets: Failed to read collection file %s" % self.disabledVideosFile, xbmc.LOGERROR)
            log("CollectSets: %s" % traceback.format_exc(), xbmc.LOGERROR)

        log("CollectSets: Number of disabled videos is %d" % len(disabledVideos))
        return disabledVideos

    def saveDisabledVideos(self, disabledVideos):
        log("CollectSets: Saving %d disabled videos" % len(disabledVideos))
        # <disabled_screensaver>
        #     <filename></filename>
        # </disabled_screensaver>
        try:
            root = ET.Element('disabled_screensaver')

            for disabledVideo in disabledVideos:
                filenameElem = ET.SubElement(root, 'filename')
                filenameElem.text = disabledVideo

            fileContent = ET.tostring(root, encoding="UTF-8")

            # Save the XML file to disk
            recordFile = xbmcvfs.File(self.disabledVideosFile, 'w')
            recordFile.write(fileContent)
            recordFile.close()
        except:
            log("CollectSets: Failed to create XML Content %s" % traceback.format_exc(), xbmc.LOGERROR)

    def getCustomCollectionSets(self):
        log("CollectSets: Loading collections %s" % self.collectSetsFile)

        customCollections = {}
        if not xbmcvfs.exists(self.collectSetsFile):
            log("CollectSets: No custom collections file exists: %s" % self.collectSetsFile)
            return customCollections

        # <collections>
        #     <collection>
        #         <name></name>
        #         <filename></filename>
        #         <image></image>
        #     </collection>
        # </collections>
        try:
            # Load the file as a string
            collectionFileRef = xbmcvfs.File(self.collectSetsFile, 'r')
            collectionStr = collectionFileRef.read()
            collectionFileRef.close()

            collectionSetElem = ET.ElementTree(ET.fromstring(collectionStr))

            # Get the collections that are in the collection set
            for elemItem in collectionSetElem.findall('collection'):
                details = {'name': None, 'filename': None, 'image': ICON, 'default': False}

                collectionName = None
                nameElem = elemItem.find('name')
                if nameElem not in [None, ""]:
                    details['name'] = nameElem.text
                    collectionName = details['name']

                filenameElem = elemItem.find('filename')
                if filenameElem not in [None, ""]:
                    details['filename'] = filenameElem.text

                imageElem = elemItem.find('image')
                if imageElem not in [None, ""]:
                    details['image'] = imageElem.text

                if collectionName in [None, ""]:
                    log("CollectSets: No name specified for collection set")
                else:
                    log("CollectSets: Loading custom collection %s (%s)" % (collectionName, filenameElem))
                    customCollections[collectionName] = details
        except:
            log("CollectSets: Failed to read collection file %s" % self.collectSetsFile, xbmc.LOGERROR)
            log("CollectSets: %s" % traceback.format_exc(), xbmc.LOGERROR)

        return customCollections

    def saveCustomCollections(self, customCollections):
        log("CollectSets: Saving %d custom collections" % len(customCollections))

        if len(customCollections) < 1:
            log("CollectSets: Removing custom collections file, as no collections")
            if xbmcvfs.exists(self.collectSetsFile):
                xbmcvfs.delete(self.collectSetsFile)
            return

        # <collections>
        #     <collection>
        #         <name></name>
        #         <filename></filename>
        #         <image></image>
        #     </collection>
        # </collections>
        try:
            root = ET.Element('collections')

            for customCollectionKey in list(customCollections.keys()):
                customCollection = customCollections[customCollectionKey]
                collectionElem = ET.SubElement(root, 'collection')

                nameElem = ET.SubElement(collectionElem, 'name')
                nameElem.text = customCollection['name']

                filenameElem = ET.SubElement(collectionElem, 'filename')
                filenameElem.text = customCollection['filename']

                if customCollection['image'] not in [None, ""]:
                    imageElem = ET.SubElement(collectionElem, 'image')
                    imageElem.text = customCollection['image']

            fileContent = ET.tostring(root, encoding="UTF-8")

            # Save the XML file to disk
            recordFile = xbmcvfs.File(self.collectSetsFile, 'w')
            recordFile.write(fileContent)
            recordFile.close()
        except:
            log("CollectSets: Failed to create XML Content %s" % traceback.format_exc(), xbmc.LOGERROR)

    # Checks a user defined collection to ensure it is correct
    def addCustomCollection(self, customXmlFile):
        log("CollectSets: Checking custom xml file: %s" % customXmlFile)

        # Try and load the collection file to ensure all the data is correct
        collectionDetails = self.loadCollection(customXmlFile, False)

        if collectionDetails in [None, ""]:
            log("CollectSets: No collection details returned for %s" % customXmlFile)
            # TODO: Show error
            return False

        collectionName = collectionDetails['name']
        if collectionName.lower() in ['aquarium', 'beach', 'clock', 'fireplace', 'miscellaneous', 'snow', 'space', 'waterfall', 'apple tv']:
            log("CollectSets: Collection name clashes %s" % collectionName)
            # We return True here, as we have already displayed an error
            msg = "%s: %s" % (ADDON.getLocalizedString(32084), collectionName)
            xbmcgui.Dialog().notification(ADDON.getLocalizedString(32005), msg, ICON, 5000, False)
            return True

        # check the number of videos
        if len(collectionDetails['videos']) < 1:
            log("CollectSets: Collection contains no videos %s" % customXmlFile)
            # TODO: Show error
            return False

        # Check each of the settings for a video, must have name, filename and primary
        for videoItem in collectionDetails['videos']:
            if videoItem['name'] in [None, ""]:
                log("CollectSets: Video without a name in collection %s" % customXmlFile)
                # TODO: Show error
                return False

            if videoItem['filename'] in [None, ""]:
                log("CollectSets: Video without a filename in collection %s" % customXmlFile)
                # TODO: Show error
                return False

            if videoItem['primary'] in [None, ""]:
                log("CollectSets: Video without a primary in collection %s" % customXmlFile)
                # TODO: Show error
                return False

        customCollections = self.getCustomCollectionSets()

        # Add check to see if it clashes with a different custom collection
        if collectionName in list(customCollections.keys()):
            log("CollectSets: Custom collection name clashes %s" % collectionName)
            # We return True here, as we have already displayed an error
            msg = "%s: %s" % (ADDON.getLocalizedString(32084), collectionName)
            xbmcgui.Dialog().notification(ADDON.getLocalizedString(32005), msg, ICON, 5000, False)
            return True

        # If we have reached here then we are OK to add the custom set, so take a copy of
        # it to the addon settings directory
        finalCustomXmlFile = os_path_join(Settings.getCustomFolder(), os_path_split(customXmlFile)[-1])
        log("CollectSets: Copy from %s to %s" % (customXmlFile, finalCustomXmlFile))
        copy = xbmcvfs.copy(customXmlFile, finalCustomXmlFile)

        if copy:
            # Now get the details that are required for the collection
            customCollections[collectionName] = {'name': collectionName, 'filename': finalCustomXmlFile, 'image': collectionDetails['image'], 'default': False}

            # save the new set of custom collections
            self.saveCustomCollections(customCollections)

        return True

    # remove a custom Collection
    def removeCustomCollection(self, name):
        log("CollectSets: Removing Custom Collection: %s" % name)

        customCollections = self.getCustomCollectionSets()

        # Make sure the one we are removing is in the collection set
        if name in list(customCollections.keys()):
            log("CollectSets: Custom collection name exists %s" % name)
            del customCollections[name]
            # save the new set of custom collections
            self.saveCustomCollections(customCollections)

    # Given a filename, finds the other videos in the same collection
    def getFilesInSameCollection(self, keyFile):
        log("CollectSets: Getting files in same collection as: %s" % keyFile)

        videoList = []
        # get all the collections
        collectionMap = self.getCollections()
        for collectionKey in list(collectionMap.keys()):
            collectionDetail = collectionMap[collectionKey]
            # Load the details about this collection
            collectionDetails = self.loadCollection(collectionDetail['filename'])
            for videoDetails in collectionDetails['videos']:
                if keyFile.lower() == videoDetails['filename'].lower():
                    log("CollectSets: Found video in collection %s" % collectionDetail['name'])
                    # Add all the videos
                    for matchedDetails in collectionDetails['videos']:
                        videoList.append(matchedDetails['filename'])
                    return videoList

        return videoList
