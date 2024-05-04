import abc
import json
import sqlite3
import requests
import datetime


class Command(abc.ABC):
    @abc.abstractmethod
    def execute(self):
        pass


class ExportMarkdownCommand(Command):
    def __init__(self, data):
        self.data = data

    def execute(self):
        markdown_document = ''
        # order notes by location
        # filter out notes without selected text
        # group by author and title and chapter
        for [asset_id, title, author, selected_text, note, represent_text, chapter, style, modified_date,
             location] in results:
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


class ExportToNotionDatabaseCommand(Command):
    def __init__(self, data, api_key, database_id):
        self.data = data
        self.api_key = api_key
        self.database_id = database_id

    def execute(self):
        for [asset_id, title, author, selected_text, note, represent_text, chapter, style, modified_date,
             location] in results:
            if represent_text is None or represent_text == '' or selected_text is None or selected_text == '':
                continue

            if author is None:
                author = 'Unknown Author'

            if title is None:
                title = 'Unknown Title'

            if chapter is None:
                chapter = 'Unknown Chapter'

            text = represent_text if represent_text is not None else selected_text
            self.create_page(author, chapter, modified_date, text, title)

    def create_page(self, author, chapter, modified_date, text, title):
        # http request to notion api
        # https://developers.notion.com/reference/post-page
        headers = {
            'Authorization': 'Bearer ' + self.api_key,
            'Notion-Version': '2022-06-28',
            'Content-Type': 'application/json'
        }
        data = {
            "parent": {
                "database_id": "7f9135bdb0c44f4195acdf377d8670a1"
            },
            "properties": {
                "Title": {
                    "title": [
                        {
                            "text": {
                                "content": title if title is not None else 'Unknown Title'
                            }
                        }
                    ]
                },
                "Chapter": {
                    "rich_text": [
                        {
                            "text": {
                                "content": chapter if chapter is not None else 'Unknown'
                            }
                        }
                    ]
                },
                "Text": {
                    "rich_text": [
                        {
                            "text": {
                                "content": text if text is not None else 'n/a'
                            }
                        }
                    ]
                },
                "Author": {
                    # author is a coma separated list of authors
                    "multi_select": [{"name": author} for author in [author.strip() for author in author.split(',')]]
                },
                "Highlighted At": {
                    "date": {
                        "start": datetime.datetime.fromtimestamp(modified_date).isoformat()
                    }
                },
            },
            "children": [
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {
                                    "content": text if text is not None else '',
                                }
                            }
                        ]
                    }
                }
            ]
        }
        response = requests.post('https://api.notion.com/v1/pages', headers=headers, data=json.dumps(data))
        if response.status_code != 200:
            print(response.json())


class Invoker:
    def __init__(self):
        self.command = None

    def set_command(self, command):
        self.command = command

    def execute_command(self):
        self.command.execute()


if __name__ == '__main__':
    # read path from config file
    config = {}
    with open('./config.json', 'r') as file:
        config = json.load(file)
    annotations_connection = sqlite3.connect(config['paths']['annotations'])
    cursor = annotations_connection.cursor()

    books_db_path = config['paths']['books']
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

    command = ExportToNotionDatabaseCommand(results, config['notion']['token'], config['notion']['databaseId'])
    invoker = Invoker()
    invoker.set_command(command)
    invoker.execute_command()
