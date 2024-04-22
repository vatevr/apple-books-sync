import sqlite3

if __name__ == '__main__':
    annotations_connection = sqlite3.connect('/Users/hamlet/Library/Containers/com.apple.iBooksX/Data/Documents/AEAnnotation/AEAnnotation_v10312011_1727_local.sqlite')
    cursor = annotations_connection.cursor()

    books_db_path = '/Users/hamlet/Library/Containers/com.apple.iBooksX/Data/Documents/BKLibrary/BKLibrary-1-091020131601.sqlite'
    books_connection = sqlite3.connect(books_db_path)
    books_cursor = books_connection.cursor()
    cursor.execute(f'ATTACH DATABASE "{books_db_path}" AS books')

    cursor.execute('''
    SELECT
        ZANNOTATIONASSETID as asset_id,
        ZTITLE as title,
        ZAUTHOR as author,
        ZANNOTATIONSELECTEDTEXT as selected_text,
        ZANNOTATIONNOTE as note,
        ZANNOTATIONREPRESENTATIVETEXT as represent_text,
        ZFUTUREPROOFING5 as chapter,
        ZANNOTATIONSTYLE as style,
        ZANNOTATIONMODIFICATIONDATE as modified_date,
        ZANNOTATIONLOCATION as location
        from ZAEANNOTATION
        left join books.ZBKLIBRARYASSET
        on ZAEANNOTATION.ZANNOTATIONASSETID = books.ZBKLIBRARYASSET.ZASSETID
        order by ZANNOTATIONASSETID, ZPLLOCATIONRANGESTART
    ;
    ''')

    results = cursor.fetchall()
    # filter out the None values
    results = [result for result in results if result[0] is not None and result[0] != '']
    markdown_document = ''

    # order notes by location
    # filter out notes without selected text
    # group by author and title and chapter
    for [asset_id, title, author, selected_text, note, represent_text, chapter, style, modified_date, location] in results:
        if selected_text is None or selected_text == '':
            continue

        if author is None:
            author = 'Unknown Author'

        if title is None:
            title = 'Unknown Title'

        if chapter is None:
            chapter = 'Unknown Chapter'

        # add a line break
        markdown_document += '\n\n\n'
        # group notes per book and chapter
        markdown_document += f'## {author} - {title}\n'
        markdown_document += f'### Chapter: {chapter}\n'
        # add a line break
        markdown_document += '\n'
        markdown_document += f'>{selected_text}\n'

    # write the markdown document to a file
    with open('./out/annotations.md', 'w') as file:
        file.write(markdown_document)
