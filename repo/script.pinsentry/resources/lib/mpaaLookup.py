import os
from urllib import parse, request
import traceback

import json

from resources.lib.settings import log


class MpaaLookup:
    def __init__(self):
        self.imdb_url_prefix = 'http://www.omdbapi.com/'
        # Flag to state that there was an error contacting the site and we should
        # not try again by changing the name slightly
        self.stopTrying = False

    # Perform a lookup for the MPAA rating, this will only return the US version
    # of the rating
    def getMpaaRatings(self, name, year=''):
        self.stopTrying = False
        mpaa = None
        if year not in [None, "", "0"]:
            # First try it as a TV Show and year
            mpaa = self.getIMDB_mpaa_by_name(name, str(year), True)

        # Check to see if a match was found, if not try without the year
        if (mpaa in [None, ""]) and (not self.stopTrying):
            mpaa = self.getIMDB_mpaa_by_name(name, '', True)

        # If no match was found as a TV Show, look for movies with this year
        if (mpaa in [None, ""]) and (year not in [None, "", "0"]) and (not self.stopTrying):
            mpaa = self.getIMDB_mpaa_by_name(name, str(year), False)

        if (mpaa in [None, ""]) and (not self.stopTrying):
            mpaa = self.getIMDB_mpaa_by_name(name, '', False)

        return mpaa

    # Get the MPAA from imdb
    def getIMDB_mpaa_by_name(self, name, year='', isTvShow=True):
        log("IdLookup: Getting IMDB Mpaa by name {}, year={}, tv={}".format(name, year, str(isTvShow)))

        clean_name = name
        # If we have been passed a file name remove the file type
        if name.endswith('.mp4') or name.endswith('.mkv') or name.endswith('.avi') or name.endswith('.mov'):
            clean_name = os.path.splitext(clean_name)[0]

        clean_name = parse.quote(clean_name)
        query = '?apikey=49d311ec&t=%s' % clean_name

        if year not in [None, '', '0']:
            query = '{}&y={}'.format(query, str(year))

        if isTvShow:
            query = '%s&type=series' % query
        else:
            query = '%s&type=movie' % query

        url = "{}{}".format(self.imdb_url_prefix, query)

        log("MpaaLookup: Using call: %s" % url)
        json_details = self._makeCall(url)

        mpaa = None
        if json_details not in [None, ""]:
            json_response = json.loads(json_details)

            if json_response.get('Response', 'False') == 'True':
                if 'Rated' in json_response:
                    mpaa = json_response.get('Rated', None)
                    if mpaa not in [None, ""]:
                        mpaa = str(mpaa)
                        log("MovieLookup: Found mpaa %s" % str(mpaa))
                        if mpaa in ["N/A"]:
                            mpaa = None
            else:
                log("MpaaLookup: No results returned for imdb mpaa search")

        return mpaa

    # Perform the API call
    def _makeCall(self, url):
        log("MpaaLookup: Making query using %s" % url)
        resp_details = None
        try:
            req = request.Request(url)
            req.add_header('Accept', 'application/json')
            response = request.urlopen(req, timeout=2)
            resp_details = response.read()
            try:
                response.close()
                log("MpaaLookup: Request returned %s" % resp_details)
            except:
                pass
        except:
            self.stopTrying = True
            log("MpaaLookup: Failed to retrieve details from {}: {}".format(url, traceback.format_exc()))

        return resp_details
