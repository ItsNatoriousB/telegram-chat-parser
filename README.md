
# telegram-chat-parser

Python script to parse a Telegram chat history backup (`JSON`) into tabular format (`CSV`). No extra packages required, only Python 3.x!
I made changes to work with Telgram's group chats and new identifiers. I've updated the old ones but left them in case needed.

## How-To Use

Using Telegram's Desktop or Web interfaces, go to the chat you want to backup, click on the options button (three dots in the upper right corner) and them click on `Export chat history`. In the dialog window, right next to `Format`, chose `JSON`. After the backup is completed, Telegram will generate a `result.json` file. This will be the input of our script.

Next, navigate to the directory where the `result.json` is located and make sure that the script is accessible, probably by placing it next to the results file. Then, run the script by typing:

```python
python3 telegram-chat-parser.py result.json
```

For each chat backup in `result.json`, a `.csv` file will be created in the same directory. The output filename is a stripped down version of the actual chat name (only letters and numbers are kept).

# Output Format

Once the script is done parsing, the result stored in `parsed.csv`

## Format:
_Some property names have changed in the Telegram export_
 - `id`: Message ID - replaced 'msg_id'
 - `from`: Sender Name - replaced 'sender'
 - `from_id`: Sender ID - replaced 'sender_id'
 - `date`: Message Date
 - `type`: Can be one of the following: `message, custom_emoji, bold, plain, underline, text, sticker, file, photo, poll, location or link`
 - `msg_content`: the text content the message, already cleaned in terms of newline and spaces; if the message was not a text (sticker, media, etc) this field will store the path pointing to the media

 ## OLD Output Format

 - ~~`msg_id`: Unique Message ID~~
 - ~~`sender`: Name of the sender~~
 - ~~`sender_id`: the unique identifier of the sender~~
 - ~~`reply_to_mesg_id`: Stores ID for replies, or -1 otherwise~~
 - ~~`msg_type`: can be one of the following: `text, sticker, file, photo, poll, location or link`~~
 - ~~`has_mention`: it will be `1` if there's a mention in the text, `0` otherwise~~
 - ~~`has_email`: it will be `1` if there's a email in the text, `0` otherwise~~
 - ~~`has_phone`: it will be `1` if there's a phone contact in the message, `0` otherwise~~
 - ~~`has_hashtag`: it will be `1` if there's a hashtag in the text, `0` otherwise~~
 - ~~`is_bot_command`: it will be `1` if the message is a bot command, `0` otherwise~~

## Contributing

I hope this little script helps you in your project! If you have any suggestions or ideas to improve it, please feel free to open an issue. Thank you!
