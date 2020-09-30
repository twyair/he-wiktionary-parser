# he-wiktionary-parser

## how to use

1. download the dump (in xml) of the hebrew wiktionary from [here](https://dumps.wikimedia.org/)
2. in python
```python
from parse import parse_pages
pages = parse_pages("path/to/wiktionary/dump.xml")
```

#### example of data extracted from the entry for the word "מִלּוֹן":
```python
Entry(
    title="מִלּוֹן",
    grammatical_info=GrammarInfo(
        pronunciation="mi'lon",
        ktiv_male="מילון",
        gender="male",
        root="מלל",
        part_of_speech="noun",
        morphology="{{מוספית|מלה|מנוקד=מִלָּה|־וֹן}}",
        declensions="ר' מִלּוֹנִים או מִלּוֹנוֹת; מִלּוֹן־, ר' מִלּוֹנֵי־ מִלּוֹנִי,",
    ),
    definitions=[
        Definition(
            definition="אוסף מילים מבוארות בשפה מסוימת, לרוב ערוּך כספר. מילון דו לשוני מכיל את אוצר המילים של שפה מסוימת, ובצד כל מילה מובאות מקבילותיה בשפה אחרת (למשל: מילון עברי־אנגלי).",
            examples=[
                Example(
                    text="\"את 'המילון החדש' ערך המילונאי והלשונאי אברהם אבן־שושן\".",
                    kind="plain-text",
                    source=[],
                )
            ],
            register=None,
            context=None,
            time_period=None,
            is_lacking=False,
            is_borrowed=False,
        )
    ],
    expressions=[
        WikiLink(text="מילון דו־לשוני", link="מלון דו לשוני"),
        WikiLink(text="מִלּוֹן כִּיס", link="מלון כיס"),
    ],
    derivatives=[
        WikiLink(text="מִלּוֹנַאי", link="מלונאי"),
        WikiLink(text="מִלּוֹנָאוּת", link="מלונאות"),
        WikiLink(text="מִלּוֹנָאִי", link="מלונאי"),
        WikiLink(text="מִלּוֹנוּת", link="מלונות"),
        WikiLink(text="מִלּוֹנִי", link="מלוני"),
    ],
    synonyms=[
        WikiLink(text="אגרון", link="אגרון"),
        WikiLink(text="לקסיקון", link="לקסיקון"),
    ],
    antonyms=[],
    translations={
        "איטלקית": ["dizionario"],
        "אנגלית": ["dictionary"],
        "גרמנית": ["Wörterbuch"],
        "יידיש": ["װערטערבוך"],
        "ספרדית": ["diccionario"],
        "ערבית": ["قاموس"],
        "פורטוגזית": ["diccionário"],
        "צרפתית": ["dictionnaire"],
        "רוסית": ["словарь"],
    },
    see_also=[WikiLink(text="קונקורדנציה", link="קונקורדנציה")],
    external_links={"ויקיפדיה": "מילון"},
    etymology=[
        ' את המילה חידש [[w:אליעזר בן־יהודה|אליעזר בן־יהודה]], שהעדיף אותה על־פני החלופה "ספר מילים". במאמר בעיתון [[w:המגיד|המגיד]], שהיה אחד הראשונים פרי עטו (משנת תר"ם), כתב: "סגולת שפת עברית, בחפצה לגזור שם חדש מפועל או משם, להוסיף בראש הפועל או השם ההוא אחת מאותיות האמנתי"ו – – נ\' האמנתי"ו הנוסף בסוף השם ישמש, לפי דברי המדקדקים החשים, לגזור שם מופשט מן השם, [...] וכן להקטין הדבר [...] אך גם נ\' האמנתי"ו הנוסף בסוף השם מורה לפעמים, לדעתי, המקום אשר בו נמצא בתוכוֹ את המושג הקרוא בשם ההוא [...] על פי הכלל הזה אשר ביארנו נוכל לגזור מהמלה \'מלה\' מלה חדשה מִלּוֹן, אשר תורה \'דבר\' או ספר המחזיק בקרבו את מלות השפה".'
    ],
    extra_info=None,
)
```
