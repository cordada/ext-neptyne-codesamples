# Neptyne Code Samples

This repository contains code samples for [Neptyne](https://www.neptyne.com).
They generally work for the core product and the 
[Add on](https://workspace.google.com/marketplace/app/neptyne_python_for_sheets/891309878867).
and where not, this will be noted in the samples.


## Samples

* [Web Search and AI](./websearch_ai_summary.py.py)

    Shows how to use Bing Search and Open AI to research a topic by doing a 
    web search and summarizing the results based on the snippets that are
    returned.

* [HN Answers](./hn_answers.py)

    Shows how to use the Hacker News API to get the recent Ask HN posts and
    then use the Open AI API to summarize the answers to the questions. Adds
    those answers to the Google Sheets and also powers a tiwtter bot.

* [Mandelbrot Set](./mandelbrot.py)

    Shows how to generate a Mandelbrot set inside of Google Sheets. Uses
    the Neptyne Python Add on to do this of course, but that outputs just
    numbers. We use conditional formatting to make it look nice.