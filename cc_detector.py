from presidio_analyzer import AnalyzerEngine, PatternRecognizer, Pattern


analyzer = AnalyzerEngine()
cc_pattern = Pattern("Credit Card", r"\b(?:4[0-9]{12}(?:[0-9]{3})?"
                                  r"|5[1-5][0-9]{14}"
                                  r"|3[47][0-9]{13}"
                                  r"|6(?:011|5[0-9]{2})[0-9]{12})\b", 0.8)
cc_recognizer = PatternRecognizer(supported_entity="CREDIT_CARD", patterns=[cc_pattern])
analyzer.registry.add_recognizer(cc_recognizer)


def detect_credit_cards(text):
    return analyzer.analyze(text=text, entities=["CREDIT_CARD"], language="en")
