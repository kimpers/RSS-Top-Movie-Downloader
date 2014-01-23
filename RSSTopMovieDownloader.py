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
        self.MOVIE_MIN_VOTES = int(self.parser.get('movie','min_votes'))
        self.RSS_URL = self.parser.get('rss','rss_url')
        self.releaseTags = self.readReleaseTagsFromFile()
        self.downloadPath = self.parser.get('download','path')
        self.downloaded = []
        with open("download.txt") as f:
            for line in f:
                self.downloaded.append(line.strip())

        
    
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
                votes = int(movie['imdbVotes'].replace(',',''))
                if (year >= self.MOVIE_MIN_YEAR and rating >= self.MOVIE_MIN_RATING and votes >= self.MOVIE_MIN_VOTES):
                    if not os.path.exists(self.downloadPath+'/'+ release + ".torrent") and movie['imdbID'] not in self.downloaded:
                        with open("download.txt", "a") as f:
                            f.write(movie['imdbID'] + "\n")
                        self.downloaded.append(movie['imdbID'])
                        os.chdir(self.downloadPath)
                        torrent = self.downloadTorrentFile(url)
                        print "DOWNLOADING " , release , " " , str(year) ," (",votes, ") ", " rating " , str(rating) , " to " , self.downloadPath
                        with open(release + ".torrent", "wb") as f:
                            f.write(torrent)
                    else:
                        print "ALREADY DOWNLOADED: ", release , " " , str(year) ," (",votes, ") ", " rating " , str(rating)
                else:
                    print "SKIPPED: ", release , " " , str(year) ," (",votes, ") ", " rating " , str(rating)
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