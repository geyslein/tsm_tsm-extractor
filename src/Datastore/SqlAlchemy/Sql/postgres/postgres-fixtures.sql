INSERT INTO public.thing (id, name, uuid, description, properties)
VALUES (1, 'MySecondThing',
        'ce2b4fb6-d9de-11eb-a236-125e5a40a845', null, '{
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
