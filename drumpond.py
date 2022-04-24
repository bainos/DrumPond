import collections
import abjad
from abjad import tag as _tag
from abjad import typings as _typings
from abjad import duration as _duration
from abjad import lyconst as _lyconst
from abjad import Leaf, Container, Context, Component
from abjad import Chord, NoteHead, Note
from abjad import Duration, Score
from abjad import tweaks as tweaksmodule


class DrumComponent(Component):

    def __init__(
        self,
        name: str = None,
        tag: _tag.Tag = None
    ) -> None:
        Component.__init__(
            self,
            name=name,
            tag=tag
        )

    def _get_drum_pitch(self, written_pitch):
        assert str(written_pitch) in _lyconst.drums
        drum_pitch = _lyconst.drums[str(written_pitch)]
        return drum_pitch

    def _set_drum_pitch(self, written_pitch):
        assert str(written_pitch) in _lyconst.drums
        drum_pitch = _lyconst.drums[str(written_pitch)]
        self._written_pitch = drum_pitch


class DrumContainer(DrumComponent, Container):
    
    def __init__(
        self,
        components=None,
        identifier: str = None,
        simultaneous: bool = False,
        name: str = None,
        tag: _tag.Tag = None,
        *arguments,
        language: str = "english",
    ) -> None:
        components = components or []
        DrumComponent.__init__(self, tag=tag)
        self._named_children: dict = {}
        self._is_simultaneous = None
        # sets name temporarily for _find_correct_effective_context:
        self._name = name
        self._initialize_components(components, language=language)
        self.identifier = identifier
        self.simultaneous = bool(simultaneous)
        # sets name permanently after _initalize_components:
        self.name = name


class DrumContext(DrumContainer, Context):
    
    def __init__(
        self,
        components=None,
        lilypond_type: str = "Context",
        simultaneous: bool = False,
        name: str = None,
        tag: _tag.Tag = None,
        *,
        language: str = "english",
    ) -> None:
        self._consists_commands: list[str] = []
        self._dependent_wrappers: list = []
        self._remove_commands: list[str] = []
        self.lilypond_type = lilypond_type
        DrumContainer.__init__(
            self,
            simultaneous=simultaneous,
            components=components,
            language=language,
            name=name,
            tag=tag,
        )


class DrumMode(DrumContext):

    def __init__(
        self,
        components=None,
        lilypond_type: str = "Voice",
        simultaneous: bool = False,
        name: str = None,
        tag: _tag.Tag = None,
        *,
        language: str = "english",
    ) -> None:
        DrumContext.__init__(
            self,
            components=components,
            language=language,
            lilypond_type=lilypond_type,
            simultaneous=simultaneous,
            name=name,
            tag=tag,
        )

    def _format_open_brackets_site(self, contributions):
        result = []
        string = r"\drummode {"
        result.extend([string])
        return result


class DrumVoice(DrumContext):

    _default_lilypond_type = "DrumVoice"

    # TODO: make keywords mandatory
    def __init__(
        self,
        components=None,
        lilypond_type: str = "DrumVoice",
        simultaneous: bool = False,
        name: str = None,
        tag: _tag.Tag = None,
        *,
        language: str = "english",
    ) -> None:
        DrumContext.__init__(
            self,
            components=components,
            language=language,
            lilypond_type=lilypond_type,
            simultaneous=simultaneous,
            name=name,
            tag=tag,
        )


class DrumStaff(DrumContext):

    _default_lilypond_type = "DrumStaff"

    # TODO: make keywords mandatory
    def __init__(
        self,
        components=None,
        lilypond_type: str = "DrumStaff",
        simultaneous: bool = False,
        name: str = None,
        tag: _tag.Tag = None,
        *arguments,
        language: str = "english",
    ) -> None:
        drumVoices = []
        if isinstance(components, DrumVoice):
            drumVoices.append(components)
        elif isinstance(components, list):
            assert len(components) == 2
            for component in components:
                if isinstance(component, DrumVoice):
                    drumVoices.append(component)
                else:
                    raise ValueError(f"{component!r} is not DrumVoice")
            voiceTwo = abjad.LilyPondLiteral(r"\voiceDOWN")
            abjad.attach(voiceTwo, drumVoices[1][0])
        else:
            raise ValueError(f"{components!r} is not DrumVoice")
        voiceOne = abjad.LilyPondLiteral(r"\voiceUP")
        abjad.attach(voiceOne, drumVoices[0][0])
        container = DrumContainer(
            drumVoices,
            simultaneous=simultaneous
        )
        dmode = DrumMode(name="drummode")
        dmode.append(container)
        DrumContext.__init__(
            self,
            components=None,
            language=language,
            lilypond_type=lilypond_type,
            simultaneous=False,
            name=name,
            tag=tag,
        )
        self.append(dmode)


class DrumLeaf(DrumComponent, Leaf):

    def __init__(
        self,
        written_duration,
        *,
        multiplier=None,
        tag: _tag.Tag = None
    ) -> None:
        DrumComponent.__init__(self, tag=tag)
        self._after_grace_container = None
        self._before_grace_container = None
        self.multiplier = multiplier
        self.written_duration = written_duration


class DrumNote(DrumLeaf, Note):

    def __init__(
        self,
        *arguments,
        language: str = "english",
        multiplier: _typings.DurationTyping = None,
        tag: _tag.Tag = None,
    ) -> None:
        assert len(arguments) in (0, 1, 2)
        if len(arguments) == 1 and isinstance(arguments[0], str):
            string = f"{{ {arguments[0]} }}"
            parsed = self._parse_lilypond_string(string, language=language)
            assert len(parsed) == 1 and isinstance(parsed[0], DrumLeaf)
            arguments = tuple([parsed[0]])
        written_pitch = None
        is_cautionary = False
        is_forced = False
        is_parenthesized = False
        if len(arguments) == 1 and isinstance(arguments[0], DrumLeaf):
            leaf = arguments[0]
            written_pitch = None
            written_duration = leaf.written_duration
            if multiplier is None:
                multiplier = leaf.multiplier
            if isinstance(leaf, DrumNote) and leaf.note_head is not None:
                written_pitch = leaf.note_head.written_pitch
                is_cautionary = leaf.note_head.is_cautionary
                is_forced = leaf.note_head.is_forced
                is_parenthesized = leaf.note_head.is_parenthesized
            # TODO: move into separate from_chord() constructor:
            elif isinstance(leaf, DrumChord):
                written_pitches = [_.written_pitch for _ in leaf.note_heads]
                if written_pitches:
                    written_pitch = written_pitches[0]
                    is_cautionary = leaf.note_heads[0].is_cautionary
                    is_forced = leaf.note_heads[0].is_forced
                    is_parenthesized = leaf.note_heads[0].is_parenthesized
        elif len(arguments) == 2:
            written_pitch, written_duration = arguments
        elif len(arguments) == 0:
            written_pitch = self._get_drum_pitch("sn")
            written_duration = _duration.Duration(1, 4)
        else:
            raise ValueError("can not initialize note from {arguments!r}.")
        DrumLeaf.__init__(self, written_duration, multiplier=multiplier, tag=tag)
        if written_pitch is not None:
            assert isinstance(written_pitch, str), repr(written_pitch)
            self.note_head = DrumNoteHead(
                written_pitch=written_pitch,
                is_cautionary=is_cautionary,
                is_forced=is_forced,
                is_parenthesized=is_parenthesized,
            )
            if isinstance(written_pitch, DrumNoteHead):
                self.note_head.tweaks = copy.deepcopy(written_pitch.tweaks)
        else:
            self._note_head = None
        if len(arguments) == 1 and isinstance(arguments[0], DrumLeaf):
            self._copy_override_and_set_from_leaf(arguments[0])


class DrumNoteHead(NoteHead):

    def __init__(
        self,
        written_pitch: str = "sn",
        is_cautionary: bool = False,
        is_forced: bool = False,
        is_parenthesized: bool = False,
        tweaks: tweaksmodule.Tweak = None,
    ) -> None:
        NoteHead.__init__(
            self,
            written_pitch=None,
            is_cautionary=is_cautionary,
            is_forced=is_forced,
            is_parenthesized=is_parenthesized,
            tweaks=tweaks,
        )
        assert str(written_pitch) in _lyconst.drums
        drum_pitch = _lyconst.drums[str(written_pitch)]
        self._written_pitch = drum_pitch

    def _get_chord_string(self) -> str:
        result = ""
        if self.written_pitch:
            if isinstance(self.written_pitch, str):
                result = self.written_pitch
            else:
                result = self.written_pitch.name
            if self.is_forced:
                result += "!"
            if self.is_cautionary:
                result += "?"
        return result


class DrumNoteHeadList(list):

    def __init__(self, argument=()):
        note_heads = [DrumNoteHead(_) for _ in argument]
        list.__init__(self, note_heads)
        self.sort()

    def __setitem__(self, i, argument):
        if isinstance(i, int):
            new_item = DrumNoteHead(argument)
            list.__setitem__(self, i, new_item)
        elif isinstance(i, slice):
            new_items = [DrumNoteHead(_) for _ in argument]
            list.__setitem__(self, i, new_items)
        self.sort()

    def append(self, item):
        if isinstance(item, DrumNoteHead):
            note_head = item
        else:
            note_head = DrumNoteHead(item)
        list.append(self, note_head)
        self.sort()

    def extend(self, items) -> None:
        note_heads = [_ if isinstance(_, DrumNoteHead) else DrumNoteHead(_) for _ in items]
        list.extend(self, note_heads)
        self.sort()

    def get(self, pitch) -> DrumNoteHead:
        result = []
        pitch = _pitch.NamedPitch(pitch)
        for note_head in self:
            assert isinstance(note_head, DrumNoteHead), repr(note_head)
            if note_head.written_pitch == pitch:
                result.append(note_head)
        count = len(result)
        if count == 0:
            raise ValueError("missing note-head.")
        elif count == 1:
            note_head = result[0]
            return note_head
        else:
            raise ValueError("extra note-head.")

    def pop(self, i=-1) -> DrumNoteHead:
        return list.pop(self, i)

    def remove(self, item):
        if isinstance(item, DrumNoteHead):
            note_head = item
        else:
            note_head = DrumNoteHead(item)
        list.remove(self, note_head)


class DrumChord(DrumLeaf, Chord):

    def __init__(
        self,
        *arguments,
        language: str = "english",
        multiplier: _typings.DurationTyping = None,
        tag: _tag.Tag = None,
    ) -> None:
        assert len(arguments) in (0, 1, 2)
        self._note_heads = DrumNoteHeadList()
        if len(arguments) == 1 and isinstance(arguments[0], str):
            string = f"{{ {arguments[0]} }}"
            parsed = self._parse_lilypond_string(string, language=language)
            assert len(parsed) == 1 and isinstance(parsed[0], DrumLeaf)
            arguments = tuple([parsed[0]])
        are_cautionary: list[bool | None] = []
        are_forced: list[bool | None] = []
        are_parenthesized: list[bool | None] = []
        if len(arguments) == 1 and isinstance(arguments[0], DrumLeaf):
            leaf = arguments[0]
            written_pitches = []
            written_duration = leaf.written_duration
            if multiplier is None:
                multiplier = leaf.multiplier
            # TODO: move to dedicated from_note() constructor:
            if isinstance(leaf, DrumNote) and leaf.note_head is not None:
                written_pitches.append(leaf.note_head.written_pitch)
                are_cautionary = [leaf.note_head.is_cautionary]
                are_forced = [leaf.note_head.is_forced]
                are_parenthesized = [leaf.note_head.is_parenthesized]
            elif isinstance(leaf, DrumChord):
                written_pitches.extend(_.written_pitch for _ in leaf.note_heads)
                are_cautionary = [_.is_cautionary for _ in leaf.note_heads]
                are_forced = [_.is_forced for _ in leaf.note_heads]
                are_parenthesized = [_.is_parenthesized for _ in leaf.note_heads]
        # TODO: move to dedicated constructor:
        elif len(arguments) == 2:
            written_pitches, written_duration = arguments
            if isinstance(written_pitches, str):
                written_pitches = [_ for _ in written_pitches.split() if _]
            elif isinstance(written_pitches, type(self)):
                written_pitches = written_pitches.written_pitches
        elif len(arguments) == 0:
            written_pitches = [self._get_drum_pitch(_) for _ in ["sn", "bd"]]
            written_duration = _duration.Duration(1, 4)
        else:
            raise ValueError(f"can not initialize chord from {arguments!r}.")
        DrumLeaf.__init__(self, written_duration, multiplier=multiplier, tag=tag)
        if not are_cautionary:
            are_cautionary = [None] * len(written_pitches)
        if not are_forced:
            are_forced = [None] * len(written_pitches)
        if not are_parenthesized:
            are_parenthesized = [None] * len(written_pitches)
        for written_pitch, is_cautionary, is_forced, is_parenthesized in zip(
            written_pitches, are_cautionary, are_forced, are_parenthesized
        ):
            if not is_cautionary:
                is_cautionary = False
            if not is_forced:
                is_forced = False
            if not is_parenthesized:
                is_parenthesized = False
            assert isinstance(written_pitch, str), repr(written_pitch)
            note_head = DrumNoteHead(
                written_pitch=written_pitch,
                is_cautionary=is_cautionary,
                is_forced=is_forced,
                is_parenthesized=is_parenthesized,
            )
            if isinstance(written_pitch, DrumNoteHead):
                note_head.tweaks = copy.deepcopy(written_pitch.tweaks)
            self._note_heads.append(note_head)
        if len(arguments) == 1 and isinstance(arguments[0], DrumLeaf):
            self._copy_override_and_set_from_leaf(arguments[0])

    def _get_summary(self):
        return " ".join([_._get_chord_string() for _ in self.note_heads])


class DrumScore(DrumContext, Score):

    def __init__(
        self,
        components=None,
        lilypond_type: str = "Score",
        simultaneous: bool = True,
        name: str = None,
        tag: _tag.Tag = None,
        *,
        language: str = "english",
    ) -> None:
        DrumContext.__init__(
            self,
            components=None,
            language=language,
            lilypond_type=lilypond_type,
            simultaneous=False,
            name=name,
            tag=tag,
        )
        if isinstance(components, DrumStaff):
            self.append(components)
        elif isinstance(components, list):
            for component in components:
                if isinstance(component, DrumStaff):
                    self.append(component)
                else:
                    raise ValueError(f"{component!r} is not DrumStaff")
        else:
            raise ValueError(f"{components!r} is not DrumStaff")


####################


chord = DrumChord()
note_heads = [
    DrumNoteHead("sn"),
    DrumNoteHead("bd"),
        ]
chord.note_heads = note_heads
chord.written_duration = Duration(1,4)

rithm = [
    abjad.Note("bd4"),
    chord,
    abjad.Note("bd4"),
    chord.__copy__(),
]
symbols = "hh8 "*8

svoice = DrumVoice(symbols.strip(), name="Symbols")
dvoice = DrumVoice(rithm, name="DrumVoice")

dstaff = DrumStaff(
    [svoice,dvoice],
    simultaneous=True,
    name="DrumStaff"
)

dscore = DrumScore(dstaff, name="DrumScore")
dstring = abjad.lilypond(dscore)

layout_file = open("./layout/layout.ly")
layout_ly = layout_file.read()
layout_file.close()

drumrests_file = open("./layout/drumrests.ly")
drumrests_ly = drumrests_file.read()
drumrests_file.close()

drumkit_file = open("./layout/drumkit.ly")
drumkit_ly = drumkit_file.read()
drumkit_file.close()

lilypond_file = abjad.LilyPondFile([
    drumrests_ly,
    drumkit_ly,
    layout_ly,
    dscore,
])
score_ly = abjad.lilypond(lilypond_file)
print(score_ly)
#abjad.show(lilypond_file)

