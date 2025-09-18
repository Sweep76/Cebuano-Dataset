from .lexer import Lexer, Token
from cebstemmer import stemmer
from .tokens import *
from .literals import *

###############################################################################
#                                                                             #
#  PARSER                                                                     #
#                                                                             #
###############################################################################
class Error(object):
    def __init__(self, error: str, fix: str, evalue: str, svalue: str | None=None):
        self.error = error
        self.correct = fix
        self.wrong_value = evalue
        self.right_value = svalue

class AST(object):
    pass


class SentencePart(AST):
    def __init__(self, left, conj=None, right=None):
        self.left = left
        self.conj = conj
        self.right = right


class NounPhrasePart(AST):
    def __init__(self, left, conj=None, right=None):
        self.left = left
        self.conj = conj
        self.right = right


class Sentence(AST):
    def __init__(self, pred, nounp=None):
        self.pred_phrase = pred
        self.noun_phrase = nounp


class PredPhrase(AST):
    def __init__(self, verbph, endadv, pred=None, midadv=None):
        self.pred = pred
        self.verb_phr = verbph
        self.adv = endadv
        self.mid_adv = midadv


class Date(AST):
    def __init__(self, kind, month, day, com=None, year=None, extra=None, sa=None):
        self.type = kind
        self.month = month
        self.day = day
        self.comma = com
        self.year = year
        self.extra = extra
        self.sa = sa


class Predicate(AST):
    def __init__(self, element):
        self.content = element


class Descriptive(AST):
    def __init__(self, element):
        self.content = element


class Adverb(AST):
    def __init__(self, element, add=None):
        self.content = element
        self.addition = add


class Time(AST):
    def __init__(self, time, num=None, day=None):
        self.noun = time
        self.number = num
        self.day = day


class NounPhrase(AST):
    def __init__(self, noun, prep, nga=None, other=None):
        self.complex_noun = noun
        self.prep_phrase = prep
        self.nga = nga
        self.clause = other


class VerbPhrase(AST):
    def __init__(self, verb, opt):
        self.complex_verb = verb
        self.opt = opt


class PrepPhrase(AST):
    def __init__(self, prep, second, noun, adv=None, extra=None):
        self.prep = prep
        self.second_prep = second
        self.noun_phrase = noun
        self.adv = adv
        self.extra = extra


class Adjective(AST):
    def __init__(self, adj, nga, ng=None):
        self.adjectives = adj
        self.nga = nga
        self.clit_ng = ng


class Word(AST):
    def __init__(self, content: Token, type):
        self.content = content
        self.type = type


class Possess(AST):
    def __init__(self, type, pos, noun=None):
        self.type = type
        self.link = pos
        self.noun = noun


class AdjOrd(AST):
    def __init__(self, mark, dash, num, nga):
        self.marker = mark
        self.dash = dash
        self.number = num
        self.nga = nga


class AdjNum(AST):
    def __init__(self, num, ka, conj=None):
        self.number = num
        self.ka = ka
        self.conj = conj


class Noun(AST):
    def __init__(self, type, adj, noun, poss, mga=None):
        self.type = type
        self.adjective = adj
        self.nouns = noun
        self.possess = poss
        self.mga = mga


class CompoundNoun(AST):
    def __init__(self, kind, noun, other=None, extra=None):
        self.type = kind
        self.other_phrase = other
        self.noun_phrase = noun
        self.extra = extra


class NounPhraseSingularPlural(AST):
    def __init__(
        self,
        type,
        noun,
        begin=None,
        ordinal=None,
        num=None,
        mga=None,
        pos=None,
        extra=None,
    ):
        self.type = type
        self.noun_sp = noun
        self.start = begin
        self.pos = pos
        self.ordinal = ordinal
        self.number = num
        self.mga = mga
        self.extra = extra


class DemPronoun(AST):
    def __init__(self, type, dem, clit=None, ordinal=None, num=None, mga=None):
        self.type = type
        self.pronoun = dem
        self.clit = clit
        self.ordinal = ordinal
        self.number = num
        self.mga = mga


class VerbComplex(AST):
    def __init__(self, prefix, root, suffix, extra=None):
        self.prefix = prefix
        self.root = root
        self.suffix = suffix
        self.extra = extra


class Parser(object):
    def __init__(self):
        self.errors = []
        self.lexer: Lexer = None
        # set current token to the first token taken from the input
        self.current_token: Token = None

    def error(self):
        raise Exception("Invalid syntax")

    def eat(self, token_type):
        # compare the current token type with the passed token
        # type and if they match then "eat" the current token
        # and assign the next token to the self.current_token,
        # otherwise raise an exception.
        # print (self.current_token.types+" "+token_type)
        # print ("eee")
        if token_type in self.current_token.types:
            self.current_token = self.lexer.get_next_token()
        else:
            self.errors.append(
                Error(
                    "Wrong syntax: " + ", ".join(self.current_token.types),
                    token_type,
                    self.current_token.value,
                )
            )

    def contain(self, words):
        result = False
        for x in self.current_token.types:
            if x in words:
                result = True
                break
        return result

    def sentence_part(self):
        """sentence_part : sentence
        | sentence (CONJ|COMMA) sentence_part
        """
        left = self.sentence()

        if TOKEN_CONJ in self.current_token.types:
            conjunct = self.current_token
            self.eat(TOKEN_CONJ)
            return self.sentence_part_extra(left, conjunct)
        elif TOKEN_COMMA in self.current_token.types:
            conjunct = self.current_token
            self.eat(TOKEN_COMMA)
            return self.sentence_part_extra(left, conjunct)
        else:
            return SentencePart(left)

    def sentence_part_extra(self, left, conj):
        right = self.sentence_part()
        return SentencePart(left, Word(conj, TOKEN_CONJ), right)

    def sentence(self):
        """sentence : pred_phrase (noun_phrase_part)?"""
        pred_phrase = self.pred_phrase()
        noun_phrase = self.noun_phrase_part()
        if pred_phrase.verb_phr is not None:
            pref = pred_phrase.verb_phr.complex_verb.prefix.content
            noun = (
                pred_phrase.verb_phr.opt
                if pred_phrase.verb_phr.opt is not None
                else noun_phrase
            )
            if (
                pref is not None
                and pref in ["nang", "mang"]
                and noun.left is not None
                and noun.left.complex_noun.type == "Singular"
                and noun.conj is None
            ):
                self.errors.append(
                    Error(
                        "Using a plural prefix for a singular noun",
                        "Use a singular prefix",
                        pref + "-",
                        ["nag-", "naga-", "mag-", "maga-"],
                    )
                )
            elif (
                pref is not None
                and pref in ["nag", "naga", "mag", "maga"]
                and noun.left is not None
                and (noun.left.complex_noun.type == "Plural" or noun.conj is not None)
            ):
                self.errors.append(
                    Error(
                        "Using a singular prefix for a plural noun",
                        "Use a plural prefix",
                        pref + "-",
                        ["nang-", "mang-"],
                    )
                )
        return Sentence(pred_phrase, noun_phrase)

    def conditions(self, conds):
        return True in conds

    def pred_phrase(self):
        """pred_phrase : verb_phrase (adverb)?
        | predicate (adverb)? verb_phrase (adverb)?
        """
        if TOKEN_VERB in self.current_token.types:
            verb_phrase = self.verb_phrase()
            end_adv = self.adverb()
            self.tenses(verb_phrase, end_adv)
            return PredPhrase(verb_phrase, end_adv)
        else:
            predicate = self.predicate()
            mid_adv = self.adverb()
            verb_phrase = (
                self.verb_phrase() if TOKEN_VERB in self.current_token.types else None
            )
            end_adv = self.adverb()
            self.tenses(verb_phrase, end_adv, mid_adv)
            return PredPhrase(verb_phrase, end_adv, predicate, mid_adv)

    def tenses_condition(self, given, one, two, root):
        words_p = words_s = correct = None
        if given in [TOKEN_NIAGING.lower(), "kaganina", "kagahapon"]:
            words_p = LITERALS_PAST_PREFIX
            words_s = LITERALS_PAST_SUFFIX
            correct = "PAST"
        elif given in [TOKEN_KARONG.lower(), "karon"]:
            words_p = LITERALS_PRESENT_PREFIX
            words_s = LITERALS_PRESENT_SUFFIX
            correct = "PRESENT"
        elif given in [TOKEN_SUNOD.lower(), "ugma"]:
            words_p = LITERALS_FUTURE_PREFIX
            words_s = LITERALS_FUTURE_SUFFIX
            correct = "FUTURE"
        if (
            one.content is not None and one.content not in words_p
        ) and two.content is None:
            self.errors.append(
                Error(
                    one.type + " from root " + root,
                    correct + "_PREFIX",
                    one.content,
                    words_p,
                )
            )
        elif one.content is None and (two.content is not None and two.content in words_s):
            self.errors.append(
                Error(
                    two.type + " from root " + root,
                    correct + "_SUFFIX",
                    two.content,
                    words_s,
                )
            )
        elif one.content is not None and two.content is not None:
            if one.content not in words_p:
                self.errors.append(
                    Error(
                        one.type + " from root " + root,
                        correct + "_PREFIX",
                        one.content,
                        words_p,
                    )
                )
            if two.content not in words_s:
                self.errors.append(
                    Error(
                        two.type + " from root " + root,
                        correct + "_SUFFIX",
                        two.content,
                        words_s,
                    )
                )

    def tenses(self, verb, end, mid=None):
        if verb is not None:
            prefix = verb.complex_verb.prefix
            suffix = verb.complex_verb.suffix
            if end is not None and type(end.content) == Time:
                noun = (
                    end.content.noun.content
                    if type(end.content.noun) != list
                    else end.content.noun[0].content
                )
                if TOKEN_HOUR not in noun.type:
                    self.tenses_condition(
                        noun.value, prefix, suffix, verb.complex_verb.root.content.value
                    )
            elif end is not None and type(end.addition) == Time:
                noun = (
                    end.addition.noun.content
                    if type(end.addition.noun) != list
                    else end.addition.noun[0].content
                )
                if TOKEN_HOUR not in noun.type:
                    self.tenses_condition(
                        noun.value, prefix, suffix, verb.complex_verb.root.content.value
                    )

    def verb_phrase(self):
        """verb_phrase : verb_complex
        | verb_complex noun_phrase_part
        | verb_complex prep_phrase
        """
        verb = self.verb_complex()
        end = None
        if (
            self.contain(
                [
                    TOKEN_DET,
                    TOKEN_PRON_POS,
                    TOKEN_PRON_POS_NG,
                    TOKEN_PRON_POS_PLURAL_NG,
                    TOKEN_PRON_PER,
                    TOKEN_DET_PLURAL,
                    TOKEN_PRON_POS_PLURAL,
                    TOKEN_PRON_PER_PLURAL,
                    TOKEN_PRON_DEM,
                    TOKEN_IKA,
                    TOKEN_NUM,
                    TOKEN_NOUN,
                    TOKEN_MONTH,
                ]
            )
            or self.current_token.value == "ka"
        ):
            end = self.noun_phrase_part()
        elif TOKEN_PREP in self.current_token.types:
            end = self.prep_phrase()
        return VerbPhrase(verb, end)

    def verb_complex(self):
        """verb_complex : (verb_prefix)? VERB (verb_suffix)?"""
        verb = self.current_token
        self.eat(TOKEN_VERB)
        word = stemmer.stem_word(verb.value, as_object=True)
        verb.value = word.root
        pref_tense = []
        suff_tense = []
        if word.prefix in LITERALS_PAST_PREFIX:
            pref_tense.append("PAST_PREFIX")
        if word.prefix in LITERALS_FUTURE_PREFIX:
            pref_tense.append("FUTURE_PREFIX")
        if word.prefix == "pag":
            pref_tense.append(TOKEN_IMPERATIVE)
        if word.prefix in LITERALS_PRESENT_PREFIX:
            pref_tense.append("PRESENT_PREFIX")
        if word.suffix in LITERALS_PAST_SUFFIX:
            suff_tense.append("PAST_SUFFIX")
        if word.suffix in LITERALS_FUTURE_SUFFIX:
            suff_tense.append("FUTURE_SUFFIX")
        if word.suffix in LITERALS_PRESENT_SUFFIX:
            suff_tense.append("PRESENT_SUFFIX")
        suff = ", ".join(suff_tense) if len(suff_tense) > 0 else "SUFFIX"
        pre = ", ".join(pref_tense) if len(pref_tense) > 0 else "PREFIX"
        if TOKEN_CLIT_Y in self.current_token.types:
            clit = self.current_token
            self.eat(TOKEN_CLIT_Y)
            return VerbComplex(
                Word(word.prefix, pre),
                Word(verb, TOKEN_VERB),
                Word(word.suffix, suff),
                Word(clit, TOKEN_CLIT_Y),
            )
        else:
            return VerbComplex(
                Word(word.prefix, pre), Word(verb, TOKEN_VERB), Word(word.suffix, suff)
            )

    def predicate(self):
        """predicate : descriptive
        | noun_phrase
        | prep_phrase
        | INT
        | empty
        """
        if self.contain(
            [
                TOKEN_DET,
                TOKEN_PRON_DEM,
                TOKEN_PRON_POS,
                TOKEN_PRON_POS_NG,
                TOKEN_PRON_POS_PLURAL_NG,
                TOKEN_PRON_PER,
                TOKEN_DET_PLURAL,
                TOKEN_PRON_POS_PLURAL,
                TOKEN_PRON_PER_PLURAL,
                TOKEN_IKA,
                TOKEN_NUM,
                TOKEN_ADJ,
                TOKEN_KA,
                TOKEN_NOUN,
                TOKEN_MONTH,
            ]
        ):
            thing = element = self.noun_phrase_part()
        elif self.contain([TOKEN_PLACE, TOKEN_ADJ, TOKEN_ADV, TOKEN_ADV_SPE]):
            thing = element = self.descriptive()
        elif TOKEN_PREP in self.current_token.types:
            thing = element = self.prep_phrase()
        elif TOKEN_INT in self.current_token.types:
            element = self.current_token
            self.eat(TOKEN_INT)
            thing = Word(element, TOKEN_INT)
        else:
            thing = None
        return Predicate(thing)

    def descriptive(self):
        """descriptive : ADJ
        | adverb
        """
        if TOKEN_ADJ in self.current_token.types:
            element = self.current_token
            self.eat(TOKEN_ADJ)
            thing = Word(element, TOKEN_ADJ)
        elif self.contain([TOKEN_PLACE, TOKEN_ADV, TOKEN_ADV_SPE]):
            thing = element = self.adverb()
        return Descriptive(thing)

    def adverb(self):
        """adverb : PLACE (time)?
        | time (ADV_SPE)?
        | ADV_SPE
        | ADV
        | alas time
        | DILI (ADV_SPE)?
        | empty
        """
        if TOKEN_PLACE in self.current_token.types:
            place = self.current_token
            self.eat(TOKEN_PLACE)
            if self.contain([TOKEN_TIME, TOKEN_NIAGING, TOKEN_SUNOD, TOKEN_KARONG]):
                time = self.time()
                return Adverb(Word(place, TOKEN_PLACE), time)
            else:
                return Adverb(Word(place, TOKEN_PLACE))
        elif TOKEN_ADV_SPE in self.current_token.types:
            element = self.current_token
            self.eat(TOKEN_ADV_SPE)
            return Adverb(Word(element, TOKEN_ADV_SPE))
        elif self.contain([TOKEN_TIME, TOKEN_NIAGING, TOKEN_SUNOD, TOKEN_KARONG, TOKEN_HOUR]):
            element = self.time()
            if TOKEN_ADV_SPE in self.current_token.types:
                opt = self.current_token
                self.eat(TOKEN_ADV_SPE)
                return Adverb(element, Word(opt, TOKEN_ADV_SPE))
            else:
                return Adverb(element)
        elif TOKEN_ADV in self.current_token.types and self.current_token.value == "alas":
            element = self.current_token
            self.eat(TOKEN_ADV)
            time = self.time()
            return Adverb(Word(element, TOKEN_ADV), time)
        elif TOKEN_ADV in self.current_token.types:
            element = self.current_token
            self.eat(TOKEN_ADV)
            return Adverb(Word(element, TOKEN_ADV))
        elif TOKEN_ADV in self.current_token.types and self.current_token.value == "dili":
            element = self.current_token
            self.eat(TOKEN_ADV)
            if TOKEN_ADV_SPE in self.current_token.types:
                opt = self.current_token
                self.eat(TOKEN_ADV_SPE)
                return Adverb(Word(element, TOKEN_ADV), Word(opt, TOKEN_ADV_SPE))
            else:
                return Adverb(Word(element, TOKEN_ADV))
        else:
            return None

    def time(self):
        """time : TIME
        | NIAGING (adj_num)? TIME_NOUN
        | SUNOD NGA (adj_num)? TIME_NOUN
        | KARONG TOKEN_TIME_NOUN_A
        | HOUR sa TIME_OF_DAY
        """
        if TOKEN_TIME in self.current_token.types:
            time = self.current_token
            self.eat(TOKEN_TIME)
            return Time(Word(time, TOKEN_TIME))
        elif TOKEN_NIAGING in self.current_token.types:
            time = self.current_token
            self.eat(TOKEN_NIAGING)
            num = self.adj_num()
            noun = self.current_token
            self.eat(TOKEN_TIME_NOUN)
            return Time(Word(time, TOKEN_NIAGING), num, Word(noun, TOKEN_TIME_NOUN))
        elif TOKEN_SUNOD in self.current_token.types:
            times = []
            times.append(Word(self.current_token, TOKEN_SUNOD))
            self.eat(TOKEN_SUNOD)
            times.append(Word(self.current_token, TOKEN_NGA))
            self.eat(TOKEN_NGA)
            num = self.adj_num()
            noun = self.current_token
            self.eat(TOKEN_TIME_NOUN)
            return Time(times, num, Word(noun, TOKEN_TIME_NOUN))
        elif TOKEN_KARONG in self.current_token.types:
            time = self.current_token
            self.eat(TOKEN_KARONG)
            noun = self.current_token
            self.eat(TOKEN_TIME_NOUN_A)
            return Time(Word(time, TOKEN_KARONG), day=Word(noun, TOKEN_TIME_NOUN_A))
        elif TOKEN_HOUR in self.current_token.types:
            time = self.current_token
            self.eat(TOKEN_HOUR)
            if self.current_token.value != "sa":
                self.errors.append(
                    Error(
                        "Preposition is not sa",
                        "Preposition should be sa",
                        self.current_token.value,
                        ["sa"],
                    )
                )
                sa = None
            else:
                sa = Word(self.current_token, TOKEN_PREP)
                self.eat(TOKEN_PREP)
            day = self.current_token
            self.eat(TOKEN_TIME_OF_DAY)
            if time.value in [
                "uno",
                "dos",
                "tres",
                "kwatro",
                "singko",
            ] and day.value not in ["ka-adlawon", "hapon"]:
                corr = ["ka-adlawon", "hapon"]
                self.errors.append(
                    Error(
                        "Wrong part of day for a particular hour",
                        "Should be " + ", or ".join(corr),
                        day.value,
                    )
                )
            if time.value in [
                "sais",
                "siete",
                "otso",
                "nuwebe",
                "diyes",
                "onse",
            ] and day.value not in ["gabi-i", "buntag"]:
                corr = ["gabi-i", "buntag"]
                self.errors.append(
                    Error(
                        "Wrong part of day for a particular hour",
                        "Should be " + ", or ".join(corr),
                        day.value,
                    )
                )
            if time.value == "dose" and day.value != "udto":
                self.errors.append(
                    Error(
                        "Wrong part of day for a particular hour",
                        "Should be udto",
                        day.value,
                        ["udto"],
                    )
                )
            return Time([Word(time, TOKEN_HOUR), sa], day=Word(day, TOKEN_TIME_OF_DAY))

    def prep_phrase(self):
        """prep_phrase : PREP (PREP)? noun_phrase_part (ADV_SPE)? (prep_phrase)?
        | empty
        """
        if TOKEN_PREP in self.current_token.types:
            prep = self.current_token
            self.eat(TOKEN_PREP)
            return self.prep_phrase_add(prep)
        else:
            return None

    def prep_phrase_add(self, prep):
        if TOKEN_PREP in self.current_token.types:
            second = self.current_token
            self.eat(TOKEN_PREP)
        else:
            second = None
        noun_phrase = self.noun_phrase_part()
        if noun_phrase is None:
            self.errors.append(
                Error(
                    "No noun phrase after preposition; type of speech found: "
                    + " ".join(self.current_token.types),
                    "Must be a noun phrase after preposition",
                    self.current_token.value,
                )
            )
        if TOKEN_ADV_SPE in self.current_token.types:
            adv = self.current_token
            self.eat(TOKEN_ADV_SPE)
        else:
            adv = None
        if TOKEN_PREP in self.current_token.types:
            extra = self.prep_phrase()
            return PrepPhrase(
                Word(prep, TOKEN_PREP),
                Word(second, TOKEN_PREP),
                noun_phrase,
                Word(adv, TOKEN_ADV_SPE),
                extra,
            )
        else:
            return PrepPhrase(Word(prep, TOKEN_PREP), Word(second, TOKEN_PREP), noun_phrase, adv)

    def date(self):
        """date : MONTH DAY (COMMA YEAR)?
        | IKA DASH DAY sa MONTH (COMMA YEAR)?
        """
        if TOKEN_MONTH in self.current_token.types:
            month = self.current_token
            self.eat(TOKEN_MONTH)
            day = self.current_token
            self.eat(TOKEN_NUM)
            if TOKEN_COMMA in self.current_token.types:
                com = self.current_token
                self.eat(TOKEN_COMMA)
                year = self.current_token
                self.eat(TOKEN_NUM)
                self.date_condition(month.value, day.value, year.value)
                return Date(
                    "English",
                    Word(month, TOKEN_MONTH),
                    Word(day, TOKEN_DAY),
                    Word(com, TOKEN_COMMA),
                    Word(year, TOKEN_YEAR),
                )
            else:
                self.date_condition(month.value, day.value)
                return Date("English", Word(month, TOKEN_MONTH), Word(day, TOKEN_DAY))

    def date_spanish(self, one, two, day):
        one.content.value = one.content.value[:-1]
        if TOKEN_PREP in self.current_token.types and self.current_token.value == "sa":
            sa = self.current_token
            self.eat(TOKEN_PREP)
        else:
            sa = None
            self.errors.append(
                Error(
                    "Misuse of preposition",
                    "Use preposition sa",
                    self.current_token.value,
                )
            )
        ex = [one, two]
        month = self.current_token
        self.eat(TOKEN_MONTH)
        if TOKEN_COMMA in self.current_token.types:
            com = self.current_token
            self.eat(TOKEN_COMMA)
            year = self.current_token
            self.eat(TOKEN_NUM)
            self.date_condition(month.value, day.value, year.value)
            return Date(
                "Spanish",
                Word(month, TOKEN_MONTH),
                Word(day, TOKEN_DAY),
                Word(com, TOKEN_COMMA),
                Word(year, TOKEN_YEAR),
                ex,
                Word(sa, TOKEN_PREP),
            )
        else:
            self.date_condition(month.value, day.value)
            return Date(
                "Spanish",
                Word(month, TOKEN_MONTH),
                Word(day, TOKEN_DAY),
                extra=ex,
                sa=Word(sa, TOKEN_PREP),
            )

    def leap_year(self, year):
        if (year % 4) == 0:
            if (year % 100) == 0:
                if (year % 400) == 0:
                    return True
                else:
                    return False
            else:
                return True
        else:
            return False

    def date_condition(self, month, day, year=None):
        if month in [
            "enero",
            "marso",
            "mayo",
            "hulyo",
            "agosto",
            "oktubre",
            "disyembre",
        ] and day not in range(1, 32):
            self.errors.append(
                Error(
                    "Way beyond the number of dates for " + month,
                    "Should be between 1 and 31",
                    day,
                )
            )
        elif month in [
            "abril",
            "hunyo",
            "septiyembre",
            "nubiyembre",
        ] and day not in range(1, 31):
            self.errors.append(
                Error(
                    "Way beyond the number of dates for " + month,
                    "Should be between 1 and 30",
                    day,
                )
            )
        elif (
            month == "pebrero"
            and day not in range(1, 30)
            and year is not None
            and self.leap_year(year) == True
        ):
            self.errors.append(
                Error(
                    "Way beyond the number of dates for " + month,
                    "Should be between 1 and 29 in a leap year",
                    day,
                )
            )
        elif (
            month == "pebrero"
            and day not in range(1, 29)
            and year is not None
            and self.leap_year(year) == False
        ):
            self.errors.append(
                Error(
                    "Way beyond the number of dates for " + month,
                    "Should be between 1 and 28",
                    day,
                )
            )

    def noun_phrase_part(self):
        """noun_phrase_part : noun_phrase
        | noun_phrase COMMA noun_phrase_part
        | noun_phrase CONJ noun_phrase
        """
        left = self.noun_phrase()
        if TOKEN_COMMA in self.current_token.types:
            conjunct = self.current_token
            self.eat(TOKEN_COMMA)
            right = self.noun_phrase_part()
            return NounPhrasePart(left, Word(conjunct, TOKEN_COMMA), right)
        elif TOKEN_CONJ in self.current_token.types:
            conjunct = self.current_token
            self.eat(TOKEN_CONJ)
            right = self.noun_phrase()
            return NounPhrasePart(left, Word(conjunct, TOKEN_CONJ), right)
        else:
            return NounPhrasePart(left)

    def noun_phrase_extras(self, ordinal=None):
        number = self.adj_num()
        if TOKEN_MGA in self.current_token.types:
            noun = self.noun_plural()
            return NounPhraseSingularPlural("Plural", noun, None, ordinal, number)
        else:
            noun = self.noun_singular()
            return NounPhraseSingularPlural("Singular", noun, None, ordinal, number)

    def noun_phrase(self):
        """noun_phrase : (noun_phrase_singular | noun_phrase_plural | dem_pron | noun_phrase_ang) (NGA sentence)? (prep_phrase)?
        | date
        | number
        | empty
        """
        if TOKEN_IKA in self.current_token.types:
            ika = Word(self.current_token, TOKEN_IKA)
            self.eat(TOKEN_IKA)
            dash = Word(Token([TOKEN_DASH], "-"), TOKEN_DASH)
            number = self.current_token
            self.eat(TOKEN_NUM)
            if TOKEN_NGA in self.current_token.types:
                nga = self.current_token
                self.eat(TOKEN_NGA)
                adj = AdjOrd(ika, dash, Word(number, TOKEN_NUM), Word(nga, TOKEN_NGA))
                if self.contain([TOKEN_KA, TOKEN_NUM, TOKEN_ADJ]):
                    return self.noun_phrase_extras(adj)
            else:
                return self.date_spanish(ika, dash, number)
        elif TOKEN_MONTH in self.current_token.types:
            return self.date()
        elif TOKEN_DET in self.current_token.types and self.current_token.value == "ang":
            noun = self.noun_phrase_ang()
            return self.noun_prep_phrase_nga(noun)
        elif self.contain([TOKEN_KA, TOKEN_NUM, TOKEN_ADJ]):
            return self.noun_phrase_extras()
        elif self.contain([TOKEN_DET, TOKEN_PRON_POS, TOKEN_PRON_PER, TOKEN_NOUN, TOKEN_PRON_POS_NG]):
            noun = self.noun_phrase_singular()
            return self.noun_prep_phrase_nga(noun)
        elif self.contain(
            [TOKEN_DET_PLURAL, TOKEN_PRON_POS_PLURAL, TOKEN_PRON_POS_PLURAL_NG, TOKEN_PRON_PER_PLURAL, TOKEN_MGA]
        ):
            noun = self.noun_phrase_plural()
            return self.noun_prep_phrase_nga(noun)
        elif TOKEN_PRON_DEM in self.current_token.types:
            noun = self.dem_pron()
            return self.noun_prep_phrase_nga(noun)
        else:
            return None

    def noun_prep_phrase_nga(self, noun):
        if TOKEN_NGA in self.current_token.types:
            nga = Word(self.current_token, TOKEN_NGA)
            self.eat(TOKEN_NGA)
            other = self.sentence()
        else:
            nga = other = None
        prep_phrase = self.prep_phrase() if TOKEN_PREP in self.current_token.types else None
        return NounPhrase(noun, prep_phrase, nga, other)

    def noun_phrase_singular(self):
        """noun_phrase_singular : (DET)? (adj_ord)? (adj_num)? noun_singular
        | PRON_PER (CLIT_Y)?
        | PRON_POS_NG (noun_singular|noun_plural)
        """
        if TOKEN_PRON_PER in self.current_token.types:
            personal = self.current_token
            self.eat(TOKEN_PRON_PER)
            if TOKEN_CLIT_Y in self.current_token.types:
                clit = Word(self.current_token, TOKEN_CLIT_Y)
                self.eat(TOKEN_CLIT_Y)
            else:
                clit = None
            return NounPhraseSingularPlural(
                "Singular", Word(personal, TOKEN_PRON_PER), extra=clit
            )
        elif TOKEN_PRON_POS_NG in self.current_token.types:
            pos = self.current_token
            self.eat(TOKEN_PRON_POS_NG)
            noun = (
                self.noun_plural()
                if TOKEN_MGA in self.current_token.types
                else self.noun_singular()
            )
            return NounPhraseSingularPlural("Singular", noun, Word(pos, TOKEN_PRON_POS_NG))
        else:
            if TOKEN_DET in self.current_token.types:
                det = self.current_token
                self.eat(TOKEN_DET)
            else:
                det = None
            ordinal = self.adj_ord() if TOKEN_IKA in self.current_token.types else None
            number = self.adj_num()
            noun = self.noun_singular()
            return NounPhraseSingularPlural(
                "Singular", noun, Word(det, TOKEN_DET), ordinal, number
            )

    def noun_phrase_plural(self):
        """noun_phrase_plural : (DET_PLURAL)? (adj_ord)? (adj_num)? noun_plural
        | PRON_PER_PLURAL (CLIT_Y)?
        | PRON_POS_PLURAL_NG (noun_singular|noun_plural)
        """
        if TOKEN_PRON_PER_PLURAL in self.current_token.types:
            personal = self.current_token
            self.eat(TOKEN_PRON_PER_PLURAL)
            if TOKEN_CLIT_Y in self.current_token.types:
                clit = Word(self.current_token, TOKEN_CLIT_Y)
                self.eat(TOKEN_CLIT_Y)
            else:
                clit = None
            return NounPhraseSingularPlural(
                "Plural", Word(personal, TOKEN_PRON_PER_PLURAL), extra=clit
            )
        elif TOKEN_PRON_POS_PLURAL_NG in self.current_token.types:
            pos = self.current_token
            self.eat(TOKEN_PRON_POS_PLURAL_NG)
            noun = (
                self.noun_plural()
                if TOKEN_MGA in self.current_token.types
                else self.noun_singular()
            )
            return NounPhraseSingularPlural(
                "Plural", noun, Word(pos, TOKEN_PRON_POS_PLURAL_NG)
            )
        else:
            if TOKEN_DET_PLURAL in self.current_token.types:
                det = self.current_token
                self.eat(TOKEN_DET_PLURAL)
            else:
                det = None
            ordinal = self.adj_ord() if TOKEN_IKA in self.current_token.types else None
            number = self.adj_num()
            noun = self.noun_plural(det)
            return NounPhraseSingularPlural(
                "Plural", noun, Word(det, TOKEN_DET_PLURAL), ordinal, number
            )

    def dem_pron(self):
        """dem_pron : PRON_DEM (CLIT_NG (adj_ord)? (adj_num)? (noun_singular | noun_plural))?"""
        dem = self.current_token
        self.eat(TOKEN_PRON_DEM)
        if TOKEN_CLIT_NG in self.current_token.types:
            clit = self.current_token
            self.eat(TOKEN_CLIT_NG)
            ordinal = self.adj_ord() if TOKEN_IKA in self.current_token.types else None
            number = self.adj_num()
            if TOKEN_MGA in self.current_token.types:
                noun = self.noun_plural()
                return DemPronoun(
                    "Plural",
                    Word(dem, TOKEN_PRON_DEM),
                    Word(clit, TOKEN_CLIT_NG),
                    ordinal,
                    number,
                    noun,
                )
            else:
                noun = self.noun_singular()
                return DemPronoun(
                    "Singular",
                    Word(dem, TOKEN_PRON_DEM),
                    Word(clit, TOKEN_CLIT_NG),
                    ordinal,
                    number,
                    noun,
                )
        else:
            return DemPronoun("", Word(dem, TOKEN_PRON_DEM))

    def noun_phrase_ang(self):
        """noun_phrase_ang : ANG (PRON_POS_NG)? (adj_ord)? (adj_num)? (noun_singular|noun_plural)
        | ANG (PRON_POS_PLURAL_NG)? (adj_ord)? (adj_num)? (noun_singular|noun_plural)
        """
        ang = self.current_token
        self.eat(TOKEN_DET)
        poss = None
        if TOKEN_PRON_POS_NG in self.current_token.types:
            poss = self.current_token
            self.eat(TOKEN_PRON_POS_NG)
        elif TOKEN_PRON_POS_PLURAL_NG in self.current_token.types:
            poss = self.current_token
            self.eat(TOKEN_PRON_POS_PLURAL_NG)
        ordinal = self.adj_ord() if TOKEN_IKA in self.current_token.types else None
        number = (
            self.adj_num()
            if TOKEN_NUM in self.current_token.types or self.current_token.value == "ka"
            else None
        )
        if TOKEN_MGA in self.current_token.types:
            noun = self.noun_plural()
            return NounPhraseSingularPlural(
                "Plural",
                noun,
                Word(ang, TOKEN_DET),
                ordinal,
                number,
                pos=Word(poss, TOKEN_PRON_POS_PLURAL_NG),
            )
        else:
            noun = self.noun_singular()
            return NounPhraseSingularPlural(
                "Singular",
                noun,
                Word(ang, TOKEN_DET),
                ordinal,
                number,
                pos=Word(poss, TOKEN_PRON_POS_NG),
            )

    def noun_singular(self):
        """noun_singular : (adjective)? (NOUN)+ (possess_singular|possess_plural|possess_general)?"""
        adj = self.adjective() if TOKEN_ADJ in self.current_token.types else None
        nouns = []
        while TOKEN_NOUN in self.current_token.types:
            nouns.append(Word(self.current_token, TOKEN_NOUN))
            self.eat(TOKEN_NOUN)
        if TOKEN_PRON_POS_N in self.current_token.types:
            poss = self.possess_singular()
        elif TOKEN_PRON_POS_PLURAL_N in self.current_token.types:
            poss = self.possess_plural()
        else:
            poss = self.possess_general()
        return Noun("Singular", adj, nouns, poss)

    def noun_plural(self, determine=None):
        """noun_plural : MGA (adjective)? (NOUN)+ (possess_singular|possess_plural|possess_general)?"""
        if determine is None:
            mga = self.current_token
            self.eat(TOKEN_MGA)
        else:
            mga = None
        adj = self.adjective() if TOKEN_ADJ in self.current_token.types else None
        nouns = []
        while TOKEN_NOUN in self.current_token.types:
            nouns.append(Word(self.current_token, TOKEN_NOUN))
            self.eat(TOKEN_NOUN)
        if TOKEN_PRON_POS_N in self.current_token.types:
            poss = self.possess_singular()
        elif TOKEN_PRON_POS_PLURAL_N in self.current_token.types:
            poss = self.possess_plural()
        else:
            poss = self.possess_general()
        return Noun("Plural", adj, nouns, poss, Word(mga, TOKEN_MGA))

    def possess_general(self):
        """possess_general : POS_LINK compound_nouns"""
        if TOKEN_POS_LINK in self.current_token.types:
            pos_link = self.current_token
            self.eat(TOKEN_POS_LINK)
            if pos_link.value == "sa" and self.contain(
                [
                    TOKEN_DET,
                    TOKEN_PRON_DEM,
                    TOKEN_PRON_POS,
                    TOKEN_PRON_POS_NG,
                    TOKEN_PRON_POS_PLURAL_NG,
                    TOKEN_PRON_PER,
                    TOKEN_DET_PLURAL,
                    TOKEN_PRON_POS_PLURAL,
                    TOKEN_PRON_PER_PLURAL,
                    TOKEN_IKA,
                    TOKEN_NUM,
                    TOKEN_ADJ,
                    TOKEN_KA,
                    TOKEN_NOUN,
                    TOKEN_MONTH,
                    TOKEN_PREP,
                ]
            ):
                return self.prep_phrase_add(pos_link)
            else:
                nouns = self.compound_nouns(pos_link)
                return Possess("General", Word(pos_link, TOKEN_POS_LINK), nouns)
        else:
            return None

    def possess_singular(self):
        """possess_singular: PRON_POS_N"""
        pos = self.current_token
        self.eat(TOKEN_PRON_POS_N)
        return Possess("Singular", Word(pos, TOKEN_PRON_POS_N))

    def possess_plural(self):
        """possess_plural: PRON_POS_PLURAL_N"""
        pos = self.current_token
        self.eat(TOKEN_PRON_POS_PLURAL_N)
        return Possess("Plural", Word(pos, TOKEN_PRON_POS_PLURAL_N))

    def compound_nouns(self, kind):
        """compound_nouns: (noun_singular|noun_plural)
        | (noun_singular|noun_plural) COMMA compound_noun()
        | (noun_singular|noun_plural) UG (noun_singular|noun_plural)
        """
        if kind.value == "ni" and TOKEN_MGA in self.current_token.types:
            self.errors.append(
                Error(
                    "Misappropriate use of possessive linker",
                    "Should use sa",
                    kind.value,
                )
            )
        noun = (
            self.noun_plural()
            if TOKEN_MGA in self.current_token.types
            else self.noun_singular()
        )
        if TOKEN_COMMA in self.current_token.types:
            extra = self.current_token
            self.eat(TOKEN_COMMA)
            other = self.compound_nouns("")
            return CompoundNoun("", noun, other, Word(extra, TOKEN_COMMA))
        elif self.current_token.value == "ug":
            extra = self.current_token
            self.eat(TOKEN_CONJ)
            other = (
                self.noun_plural()
                if TOKEN_MGA in self.current_token.types
                else self.noun_singular()
            )
            return CompoundNoun("", noun, other, Word(extra, TOKEN_CONJ))
        else:
            return CompoundNoun("", noun)

    def adj_ord(self):
        """adj_ord : IKA DASH NUM NGA"""
        ika = Word(self.current_token, TOKEN_IKA)
        self.eat(TOKEN_IKA)
        dash = Word(Token([TOKEN_DASH], "-"), TOKEN_DASH)
        number = self.current_token
        self.eat(TOKEN_NUM)
        nga = self.current_token
        self.eat(TOKEN_NGA)
        return AdjOrd(ika, dash, Word(number, TOKEN_NUM), Word(nga, TOKEN_NGA))

    def adj_num(self):
        """adj_num : NUM KA
        | KA NUM AN (UG NUM)? KA
        """
        if TOKEN_NUM in self.current_token.types:
            number = self.current_token
            self.eat(TOKEN_NUM)
            if TOKEN_PRON_PER in self.current_token.types:
                ka = self.current_token
                self.eat(TOKEN_PRON_PER)
                return AdjNum(Word(number, TOKEN_NUM), Word(ka, TOKEN_KA))
            else:
                return Word(number, TOKEN_NUM)
        elif self.current_token.value == "ka":
            give = []
            give.append(Word(self.current_token, TOKEN_KA))
            self.eat(TOKEN_PRON_PER)
            give.append(Word(self.current_token, TOKEN_NUM))
            self.eat(TOKEN_NUM)
            give.append(Word(self.current_token, TOKEN_AN))
            self.eat(TOKEN_AN)
            if TOKEN_CONJ in self.current_token and self.current_token.value == TOKEN_UG:
                conj = self.current_token
                self.eat(TOKEN_UG)
                give.append(Word(self.current_token, TOKEN_NUM))
                self.eat(TOKEN_NUM)
            else:
                conj = None
            ka = self.current_token
            self.eat(TOKEN_KA)
            return AdjNum(give, Word(ka, TOKEN_KA), Word(conj, TOKEN_CONJ))
        else:
            return None

    def adjective(self):
        """adjective : ADJ ((NGA|NG) ADJ)* (NG|NGA)?"""
        adjectives = []
        nga = []
        current = self.current_token
        adjectives.append(Word(current, TOKEN_ADJ))
        self.eat(TOKEN_ADJ)
        extra = stemmer.stem_word(current.value, as_object=True).prefix
        while TOKEN_NGA in self.current_token.types or extra == "ng":
            if TOKEN_NGA in self.current_token.types:
                nga.append(Word(self.current_token, TOKEN_NGA))
                self.eat(TOKEN_NGA)
            else:
                nga.append(Word(Token(["NG_PREFIX"], extra), "NG_PREFIX"))
            if TOKEN_ADJ in self.current_token.types:
                current = self.current_token
                extra = stemmer.stem_word(current.value, as_object=True).prefix
                adjectives.append(Word(current, TOKEN_ADJ))
                self.eat(TOKEN_ADJ)
        return Adjective(adjectives, nga)

    def parse(self, text: str):
        """
        sentence_part : sentence
                      | sentence (CONJ|COMMA) sentence_part
        sentence : pred_phrase (noun_phrase_part)?
        pred_phrase : verb_phrase (adverb)?
                    | predicate (adverb)? verb_phrase (adverb)?
        verb_phrase : verb_complex (noun_phrase_part)?
                    | verb_complex (prep_phrase)?
        predicate : descriptive
                  | noun_phrase_part
                  | prep_phrase
                  | INT
        descriptive : ADJ
                    | adverb
        adverb : PLACE (time)?
                | time (ADV_SPE)?
                | ADV_SPE
                | ADV
                | alas time
                | DILI (ADV_SPE)?
                | empty
        time : TIME
                 | NIAGING (adj_num)? TIME_NOUN
                 | SUNOD NGA (adj_num)? TIME_NOUN
                 | KARONG TOKEN_TIME_NOUN_A
                 | HOUR sa TIME_OF_DAY
        date : MONTH DAY (COMMA YEAR)?
                | IKA DASH DAY sa MONTH (COMMA YEAR)?
        prep_phrase : PREP (PREP)? noun_phrase_part (ADV_SPE)? (prep_phrase)?
                    | empty
        noun_phrase_part : noun_phrase
                            | noun_phrase COMMA noun_phrase_part
                            | noun_phrase CONJ noun_phrase
        noun_phrase : (noun_phrase_singular | noun_phrase_plural | dem_pron | noun_phrase_ang) (NGA sentence)? (prep_phrase)?
                       | date
                       | number
                       | empty
        noun_phrase_singular : (DET) (adj_ord)? (adj_num)? noun_singular
                             | PRON_PER
                             | PRON_POS_NG (noun_singular|noun_plural)
        noun_phrase_plural : (DET_PLURAL) (adj_ord)? (adj_num)? noun_plural
                           | PRON_PER_PLURAL
                           | PRON_POS_PLURAL_NG (noun_singular|noun_plural)
        noun_phrase_ang : ANG (PRON_POS_NG)? (adj_ord)? (adj_num)? (noun_singular|noun_plural)
                           | ANG (PRON_POS_PLURAL_NG)? (adj_ord)? (adj_num)? (noun_singular|noun_plural)
        dem_pron : dem_pron : PRON_DEM (CLIT_NG (adj_ord)? (adj_num)? (noun_singular | noun_plural))?
        noun_singular : (adjective)? (NOUN)+ (possess_singular|possess_plural|possess_general)?
        noun_plural : MGA (adjective)? (NOUN)+ (possess_singular|possess_plural|possess_general)?
        possess_singular: PRON_POS_N
        possess_plural: PRON_POS_PLURAL_N
        possess_general : POS_LINK compound_nouns
        compound_nouns: (noun_singular|noun_plural)
                            | (noun_singular|noun_plural) COMMA compound_noun()
                            | (noun_singular|noun_plural) UG (noun_singular|noun_plural)
        adj_ord : IKA DASH NUM (NGA | NG)
        adj_num : NUM KA
                | KA NUM AN (UG NUM)? KA
        verb_complex : (verb_prefix)? VERB (verb_suffix)? ((PRON_PER)CLIT_Y)?
        verb_prefix : VERB_PREF_PRES
                    | VERB_PREF_PAST
                    | VERB_PREF_FUT
        verb_suffix : A
                    | HA
                    | HI
                    | VERB_SUFF_PRES
                    | VERB_SUFF_PAST
                    | VERB_SUFF_FUT
        adjective : ADJ (NGA ADJ)* (CLIT_NG|NGA)?
        """
        self.errors = []
        self.lexer = Lexer(text)
        self.current_token = self.lexer.get_next_token()
        node = self.sentence_part()
        # if self.current_token.type != TOKEN_EOF:
        #    self.error()

        return self.errors, node