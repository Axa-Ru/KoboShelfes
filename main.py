#!/usr/bin/python3
# coding=utf-8# -*- coding: utf-8 -*-

__author__ = 'axa'

import os
import sqlite3
import sys
import uuid
from datetime import datetime

SDCardPathMount = '/home/axa/Media/axa/KoboSD'
KoboPathMount = '/home/axa/Media/axa/KOBOeReader'
DBPath = '/home/axa/Media/axa/KOBOeReader/.kobo/KoboReader.sqlite'
BooksRoot = 'Books'
BookShelfs = set()


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
                            (   CreationDate,
                                id,
                                InternalName,
                                LastModified,
                                Name,
                                Type,
                                _IsDeleted,
                                _IsVisible,
                                _IsSynced
                            )
                            VALUES(?,?,?,?,?,?,?,?,?)''',
                            (   v_CreationDate,
                                v_uuidShelf,
                                v_InternalName,
                                v_LastModified,
                                v_Name,
                                v_Type,
                                v__IsDeleted,
                                v__IsVisible,
                                v__IsSynced
                           )
                         )


# noinspection SqlResolve
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
                        (   ShelfName,
                            ContentId,
                            DateModified,
                            _IsDeleted,
                            _IsSynced
                        )
                        VALUES(?,?,?,?,?)''',
                        (
                            v_ShelfName,
                            v_ContentId,
                            v_DateModified,
                            v__IsDeleted,
                            v__IsSynced
                        )
                      )


def main(argv):
    conn = sqlite3.connect(DBPath)
    c = conn.cursor()
    # Очистить содержимое таблицы "Shelf"
    c.execute("DELETE FROM Shelf")
    # Очистить содержимое таблицы "ShelfContent"
    c.execute("DELETE FROM ShelfContent")

    # добавляем полки и книги из SD карты
    SDCardPathBooks = SDCardPathMount + '/' + BooksRoot
    for dirName, subdirList, file_list in os.walk(SDCardPathBooks):
        file_list = [fi for fi in file_list if fi.lower().endswith('.epub')]

        location = 'file:///mnt/sd'
        book_path = dirName.replace(SDCardPathMount, '')
        for f_name in file_list:
            addBook(location, book_path, f_name, c)

    conn.commit()
    conn.execute("VACUUM")
    conn.close()


if __name__ == "__main__":
    main(sys.argv)
