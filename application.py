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

    for result in results:
        markdown_document += f'## {result[1]} by {result[2]}\n'
        markdown_document += f'{result[3]}\n'
        markdown_document += f'Chapter: {result[6]}\n'
        markdown_document += f'Style: {result[7]}\n'

        # add a line break
        markdown_document += '\n\n\n'

    # write the markdown document to a file
    with open('./out/annotations.md', 'w') as file:
        file.write(markdown_document)
