INSERT INTO THING (ID, NAME, UUID, DESCRIPTION, PROPERTIES)
VALUES (1, 'My Oracle Thing', '7f384bcc-ea5d-11eb-9d12-54e1ad7c5c19', null, '{
  "parsers": [
    {
      "type": "AnotherCustomParser",
      "settings": {
        "delimiter": ",",
        "footlines": 0,
        "headlines": 1,
        "timestamp": {
          "date": {
            "pattern": "^(\\d{4})-(\\d{2})-(\\d{2})",
            "position": 1,
            "replacement": "$1-$2-$3"
          },
          "time": {
            "pattern": "(\\d{2}):(\\d{2}):(\\d{2})$",
            "position": 1,
            "replacement": "$1:$2:$3"
          }
        }
      }
    },
    {
      "type": "MyCustomParser"
    },
    {
      "type": "CsvParser",
      "settings": {
        "timestamp_format": "%Y/%m/%d %H:%M:%S",
        "header": 3,
        "delimiter": ",",
        "timestamp_column": 1,
        "skipfooter": 1
      }
    }
  ]
}');
