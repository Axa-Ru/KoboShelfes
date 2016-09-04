#!/usr/bin/python3
# coding=utf-8# -*- coding: utf-8 -*-

__author__ = 'axa'
__version__ = '160904'

import os
import os.path
import sqlite3
import sys
import uuid
from datetime import datetime
from sys import platform
import subprocess
import argparse


Debug = False
BookShelfs = set()


# -----------------------------------------------------
#
#
def parseCL():
    parser = argparse.ArgumentParser()
    parser.add_argument('--ereader', type=str, help='Mount point of eReader', default='')
    parser.add_argument('--sd', type=str, help='Mount point of SD card', default='')
    parser.add_argument('--rbook', type=str, choices=['on', 'off'], default='off',
                        help='Enabling/disabling adding book from eReader memory. Disabled by default')
    parser.add_argument('--sdbook', type=str, choices=['on', 'off'], default='on',
                        help='Enabling/disabling adding book from SD card memory. Enabled by default')
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
                    args.ereader = dev
                elif os.path.isdir(dev + '/koboExtStorage'):
                    args.sd = dev
    elif platform == 'win32':
        # для windows точки монтирования нужно указывать вручную в командной строке
        pass
    elif Debug:
        args.sd = '/home/axa/Media/axa/KoboSD'
        args.ereader = '/home/axa/Media/axa/KOBOeReader'
    else:
        print('Upssss.... I dont know this host')
        quit()

    if args.ereader == '' or args.sd == '':
        print('Check mount Reader and SD card or use command line switches')
        quit()


# -----------------------------------------------------
#
#
def showSettings(args):
    print('eReader mount point: ', args.ereader)
    print('SD card mount point: ', args.sd)
    print('Add books from eReader: ', args.rbook)
    print('Add books from SD card: ', args.sdbook)


# -----------------------------------------------------
#
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
    if args.ereader == '' or args.sd == '':
        detectUSBDrive(args)
    if args.showsettings:
        showSettings(args)
        quit()
    if args.version:
        print('Version ', __version__)
        quit()

    db_path = args.ereader + '/.kobo/KoboReader.sqlite'
    BooksRoot = 'Books'

    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    # Очистить содержимое таблицы "Shelf"
    c.execute("DELETE FROM Shelf")
    # Очистить содержимое таблицы "ShelfContent"
    c.execute("DELETE FROM ShelfContent")

    # добавляем полки и книги из SD карты
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
