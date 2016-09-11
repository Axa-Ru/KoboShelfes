#!/usr/bin/python3
# coding=utf-8# -*- coding: utf-8 -*-

__author__ = 'axa'
__version__ = '0.91 build 2016-09-10'

# git: https://github.com/Axa-Ru/KoboShelfes/blob/master/KoboShelf.py
# description:
#       http://axa-ru.blogspot.ru/2016/09/kobo.html
#       http://www.the-ebook.org/forum/viewtopic.php?t=31294


import os
import os.path
import sqlite3
import sys
import uuid
from datetime import datetime
from sys import platform
import subprocess
import argparse
import string

Debug = False
BookShelfs = set()


# -----------------------------------------------------
#  Wait for press <Enter_key> and exit
#  This solution for Windows prevents closing window
def closeApplication():
    input('\nPress <Enter> for close Application')
    exit()


# -----------------------------------------------------
#  Parsing Command Line
#
def parseCL():
    parser = argparse.ArgumentParser()
    parser.add_argument('--onboard', type=str, help='Mount point of eReader', default='')
    parser.add_argument('--sd', type=str, help='Mount point of SD card', default='')
    parser.add_argument('--onboard_sw', type=str, choices=['on', 'off'], default='on',
                        help='Enabling/disabling adding book from eReader onboard memory. Enabled by default')
    parser.add_argument('--sd_sw', type=str, choices=['on', 'off'], default='on',
                        help='Enabling/disabling adding book from SD card memory. Enabled if SD card present')
    parser.add_argument('-s', '--showsettings', action='count',
                        help='Display settings and exit. Reader must be connected.')
    parser.add_argument('-v', '--version', action='version', version='Version: ' + __version__)
    return parser.parse_args()


# -----------------------------------------------------
# Determining mount point of KoboeReader and SD card
#
def detectUSBDrive(args):
    if platform == 'linux' and not Debug:
        try:
            df = subprocess.check_output("df --type=vfat --output=target | grep /", shell=True).decode("utf-8")
        except:
            pass
        else:
            for dev in df.split('\n'):
                if os.path.basename(dev) == 'KOBOeReader':
                    args.onboard = dev
                elif os.path.isdir(dev + '/koboExtStorage'):
                    args.sd = dev
    elif platform == 'win32':
        # Import for windows platform
        from ctypes import windll
        bitmask = windll.kernel32.GetLogicalDrives()
        for letter in string.ascii_uppercase:
            if bitmask & 1:
                if os.path.isdir(letter + ':/.kobo'):
                    args.onboard = letter + ':'
                elif os.path.isdir(letter + ':/koboExtStorage'):
                    args.sd = letter + ':'
            bitmask >>= 1
        pass
    elif Debug:
        args.sd = '/home/axa/Media/axa/KoboSD'
        args.onboard = '/home/axa/Media/axa/KOBOeReader'
    else:
        print('Upssss.... I dont know this host')
        closeApplication()

    if args.onboard == '':
        print('Can\'t find Kobo eReader.\n'
              'Check mount Reader or use command line switches')
        closeApplication()


# -----------------------------------------------------
#  Simply show current setting
#
def showSettings(args):
    print('eReader mount point: ', args.onboard)
    print('SD card mount point: ', args.sd)
    print('Add books from eReader: ', args.onboard_sw)
    print('Add books from SD card: ', args.sd_sw)


# -----------------------------------------------------
# Adding Book shelf to BD
#
def addBookShelf(book_shelf, cursorSQL):
    if book_shelf not in BookShelfs:
        BookShelfs.add(book_shelf)
        print('BookShelf: %s' % book_shelf)
        v_CreationDate = '1970-01-01T00:00:00Z'
        v_uuidShelf = str(uuid.uuid4())
        v_InternalName = book_shelf
        v_LastModified = '1970-01-01T00:00:00Z'
        v_Name = book_shelf
        v_Type = 'Custom'
        v__IsDeleted = "False"
        v__IsVisible = "True"
        v__IsSynced = "True"

        cursorSQL.execute('''INSERT INTO Shelf
          (CreationDate, id, InternalName, LastModified, Name,
           Type, _IsDeleted, _IsVisible, _IsSynced)
          VALUES(?,?,?,?,?,?,?,?,?)''',
          ( v_CreationDate, v_uuidShelf, v_InternalName, v_LastModified,
            v_Name, v_Type, v__IsDeleted, v__IsVisible, v__IsSynced)
                          )


# -----------------------------------------------------
# noinspection SqlResolve
#
def addBook(location, book_path, f_name, cursorSQL):
    book_shelf = os.path.basename(book_path)
    addBookShelf(book_shelf, cursorSQL)
    book_full_path = location + book_path + '/' + f_name
    book_full_path = book_full_path.replace("\\", "/")
    print('\t%s' % book_full_path)
    v_ShelfName = book_shelf
    v_ContentId = book_full_path
    v_DateModified = datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f%z')[:-3]
    v__IsDeleted = "False"
    v__IsSynced = "False"
    cursorSQL.execute('''INSERT INTO ShelfContent
      (ShelfName, ContentId, DateModified, _IsDeleted, _IsSynced)
      VALUES(?,?,?,?,?)''',
      ( v_ShelfName, v_ContentId, v_DateModified, v__IsDeleted, v__IsSynced )
                      )


# -----------------------------------------------------
#
#
def main(argv):
    args = parseCL()
    if args.onboard == '' or args.sd == '':
        detectUSBDrive(args)
    if args.showsettings:
        showSettings(args)
        closeApplication()

    db_path = args.onboard + '/.kobo/KoboReader.sqlite'
    BooksRoot = 'Books'

    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    # Clear "Shelf" Table
    c.execute("DELETE FROM Shelf")
    # Clear "ShelfContent" Table
    c.execute("DELETE FROM ShelfContent")

    if args.onboard_sw == 'on':
        # Add Shelves and books from internal memory
        books = args.onboard + '/' + BooksRoot
        for dirName, subdirList, file_list in os.walk(books):
            file_list = [fi for fi in file_list if fi.lower().endswith('.epub')]
            location = 'file:///mnt/onboard'
            book_path = dirName.replace(args.onboard, '')
            for f_name in file_list:
                addBook(location, book_path, f_name, c)

    if args.sd_sw == 'on':
        # Add Shelves and books from SD card
        SDCardPathBooks = args.sd + '/' + BooksRoot
        for dirName, subdirList, file_list in os.walk(SDCardPathBooks):
            file_list = [fi for fi in file_list if fi.lower().endswith('.epub')]
            location = 'file:///mnt/sd'
            book_path = dirName.replace(args.sd, '')
            for f_name in file_list:
                addBook(location, book_path, f_name, c)

    conn.commit()
    # conn.execute("VACUUM")
    conn.close()


if __name__ == "__main__":
    main(sys.argv)
    closeApplication()
