'''
Created on Feb 25, 2013
Downloads movies from Torrent RSS feeds depending on IMDB rating 
@author: Kim
'''

import httplib2,json,string,os
from datetime import date
import xml.etree.ElementTree as ET
from ConfigParser import SafeConfigParser

class MovieParser:
    def __init__(self):
        self.parser = SafeConfigParser()
        self.parser.read('config.cfg')
        self.MOVIE_MIN_YEAR = int(self.parser.get('movie','min_year'))
        self.MOVIE_MIN_RATING = float(self.parser.get('movie','min_rating'))
        self.RSS_URL = self.parser.get('rss','rss_url')
        self.releaseTags = self.readReleaseTagsFromFile()
        self.downloadPath = self.parser.get('download','path')
    
    def parseRSS(self):
        rssStr = self.getUrlContent(self.RSS_URL)
        xml = ET.fromstring(rssStr)
        for channel in xml:
            for item in channel.findall('item'):
                title =  item.find('title').text
                url = item.find('link').text
                self.parseMovieAndDownload(title, url)

        
    def parseMovieAndDownload(self, release, url):
        (name, year) = self.parseMovieNameFromRelease(release)
        movieJson = self.getMovieFromTitle(name,year)
        movie = self.parseJson(movieJson)
        
        # Continue if lookup was successful
        if movie != None and movie['Response'] == 'True':
            try:
                year = int(movie['Year'])
                rating = float( movie['imdbRating'])
                if (year >= self.MOVIE_MIN_YEAR and rating >= self.MOVIE_MIN_RATING):
                    if not os.path.exists(self.downloadPath+'/'+ release + ".torrent"):
                        os.chdir(self.downloadPath)
                        torrent = self.downloadTorrentFile(url)
                        print "Downloading " + release + " (" + str(year) + ") rating " + str(rating) + " to " + self.downloadPath
                        with open(release + ".torrent", "wb") as f:
                            f.write(torrent)
                    else:
                        print release ,"(",rating ,") already downloaded"
                else:
                    print release ,"(",rating ,") skipped"
            except ValueError:
                print "Error parsing rating and year"       

    def downloadTorrentFile(self, url):
        h = httplib2.Http(disable_ssl_certificate_validation=True)
        (resp, content) = h.request(url, "GET")
        return content
    def getUrlContent(self,url):
        h = httplib2.Http(disable_ssl_certificate_validation=True)
        (resp, content) = h.request(url, "GET")
        return content.decode("utf-8")
    
    def parseJson(self,jsonStr):
        jsonData =json.loads(jsonStr,"utf-8")
        return jsonData
    
    def getMovieFromTitle(self, name, year):
        url = 'http://www.omdbapi.com?t=' + name.replace(" ", "%20")
        if (year != None):
            url +='&y=' + str(year)
        return self.getUrlContent(url)
    
    def getMovieFromImdbId(self,imdbid):
        return self.getUrlContent('http://www.omdbapi.com?i=' + imdbid)
    
    def readReleaseTagsFromFile(self):
        with open("releasetags.txt") as f:
            lines = f.readlines()
        return lines
            
    def parseMovieNameFromRelease(self,releaseStr):
        wordList = releaseStr.split('.')
        movieName = ""
        movieYear = None
        loop = True
        for word in wordList:
            for tag in self.releaseTags:
                if string.lower(word) == string.lower(tag.rstrip('\r\n')):
                    loop = False
                    break
            if loop:
                if word.isdigit() and int(word) >= 1900 and int(word) <= date.today().year:
                    movieYear = int(word)
                else:
                    movieName += word + " "
            else:
                break
        movieName = movieName[:-1]
        return (movieName,movieYear)
        
def main():
    mp= MovieParser()
    mp.parseRSS();
    
if __name__ == '__main__':
    main()