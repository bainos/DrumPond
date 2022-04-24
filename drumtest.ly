\version "2.23.2"
\language "english"
#(define (rest-score r)
  (let ((score 0)
    (yoff (ly:grob-property-data r 'Y-offset))
    (sp (ly:grob-property-data r 'staff-position)))
    (if (number? yoff)
    (set! score (+ score 2))
    (if (eq? yoff 'calculation-in-progress)
        (set! score (- score 3))))
    (and (number? sp)
     (<= 0 2 sp)
     (set! score (+ score 2))
     (set! score (- score (abs (- 1 sp)))))
    score))

#(define (merge-rests-on-positioning grob)
  (let* ((can-merge #f)
     (elts (ly:grob-object grob 'elements))
     (num-elts (and (ly:grob-array? elts)
            (ly:grob-array-length elts)))
     (two-voice? (= num-elts 2)))
    (if two-voice?
    (let* ((v1-grob (ly:grob-array-ref elts 0))
           (v2-grob (ly:grob-array-ref elts 1))
           (v1-rest (ly:grob-object v1-grob 'rest))
           (v2-rest (ly:grob-object v2-grob 'rest)))
      (and
       (ly:grob? v1-rest)
       (ly:grob? v2-rest)                
       (let* ((v1-duration-log (ly:grob-property v1-rest 'duration-log))
          (v2-duration-log (ly:grob-property v2-rest 'duration-log))
          (v1-dot (ly:grob-object v1-rest 'dot))
          (v2-dot (ly:grob-object v2-rest 'dot))
          (v1-dot-count (and (ly:grob? v1-dot)
                     (ly:grob-property v1-dot 'dot-count -1)))
          (v2-dot-count (and (ly:grob? v2-dot)
                     (ly:grob-property v2-dot 'dot-count -1))))
         (set! can-merge
           (and 
            (number? v1-duration-log)
            (number? v2-duration-log)
            (= v1-duration-log v2-duration-log)
            (eq? v1-dot-count v2-dot-count)))
         (if can-merge
         ;; keep the rest that looks best:
         (let* ((keep-v1? (>= (rest-score v1-rest)
                      (rest-score v2-rest)))
            (rest-to-keep (if keep-v1? v1-rest v2-rest))
            (dot-to-kill (if keep-v1? v2-dot v1-dot)))
           ;; uncomment if you're curious of which rest was chosen:
           ;;(ly:grob-set-property! v1-rest 'color green)
           ;;(ly:grob-set-property! v2-rest 'color blue)
           (ly:grob-suicide! (if keep-v1? v2-rest v1-rest))
           (if (ly:grob? dot-to-kill)
               (ly:grob-suicide! dot-to-kill))
           (ly:grob-set-property! rest-to-keep 'direction 0)
           (ly:rest::y-offset-callback rest-to-keep)))))))
    (if can-merge
    #t
    (ly:rest-collision::calc-positioning-done grob))))


drumPitchNames = #'(   (footpedal . footpedal)
   (kick . kick)
   (kicka . kicka)
   (kickb . kickb)
   (kickc . kickc)
   (bassdrum . kick)
   (bassdruma . kicka)
   (bassdrumb . kickb)
   (bassdrumc . kickc)
   (floortom . floortom)
   (floortoma . floortoma)
   (floortomb . floortomb)
   (floortomc . floortomc)
   (floortomd . floortomd)
   (snare . snare)
   (snarea . snarea)
   (snareb . snareb)
   (snarec . snarec)
   (snared . snared)
   (snaree . snaree)
   (midtom . midtom)
   (midtoma . midtoma)
   (midtomb . midtomb)
   (midtomc . midtomc)
   (midtomd . midtomd)
   (hightom . hightom)
   (hightoma . hightoma)
   (hightomb . hightomb)
   (hightomc . hightomc)
   (hightomd . hightomd)
   (ride . ride)
   (ridea . ridea)
   (rideb . rideb)
   (ridec . ridec)
   (hihat . hihat)
   (hihata . hihata)
   (hihatb . hihatb)
   (hihatc . hihatc)
   (hihatd . hihatd)
   (hihate . hihate)
   (hihatf . hihatf)
   (crash . crash)
   (crasha . crasha)
   (crashb . crashb)
   (hf . footpedal)
   (bd . kick)
   (bda . kicka)
   (bdb . kickb)
   (bdc . kickc)
   (ft . floortom)
   (fta . floortoma)
   (ftb . floortomb)
   (ftc . floortomc)
   (ftd . floortomd)
   (sn . snare)
   (sna . snarea)
   (snb . snareb)
   (snc . snarec)
   (snd . snared)
   (sne . snaree)
   (mt . midtom)
   (mta . midtoma)
   (mtb . midtomb)
   (mtc . midtomc)
   (mtd . midtomd)
   (ht . hightom)
   (hta . hightoma)
   (htb . hightomb)
   (htc . hightomc)
   (htd . hightomd)
   (ri . ride)
   (ria . ridea)
   (rib . rideb)
   (ric . ridec)
   (hh . hihat)
   (hha . hihata)
   (hhb . hihatb)
   (hhd . hihatd)
   (hhe . hihate)
   (hhf . hihatf)
   (hho . hihatopen)
   (hhao . hihatc)
   (cr . crash)
   (cra . crasha)
   (crb . crashb)
)

#(define dbdrums '(
   (footpedal cross #f -5)
   (kick () #f -5)
   (kicka () #f -5)
   (kickb () #f -5)
   (kickc () #f -5)
   (floortom () #f -1)
   (floortoma () #f -1)
   (floortomb () #f -1)
   (floortomc () #f -1)
   (floortomd () #f -1)
   (snare () #f 0)
   (snarea () #f 0)
   (snareb () #f 0)
   (snarec cross #f 0)
   (snared () #f 0)
   (snaree () #f 0)
   (midtom () #f 1)
   (midtoma () #f 1)
   (midtomb () #f 1)
   (midtomc () #f 1)
   (midtomd () #f 1)
   (hightom () #f 3)
   (hightoma () #f 3)
   (hightomb () #f 3)
   (hightomc () #f 3)
   (hightomd () #f 3)
   (ride cross #f 4)
   (ridea cross #f 4)
   (rideb triangle #f 4)
   (ridec cross #f 4)
   (hihat cross #f 5)
   (hihata xcircle #f 5)
   (hihatb cross "open" 5)
   (hihatc xcircle "open" 5)
   (hihatd cross #f 5)
   (hihate cross "stopped" 5)
   (hihatf cross #f 5)
   (hihatopen cross "open" 5)
   (crash cross #f 6)
   (crasha cross #f 6)
   (crashb cross "stopped" 6)
))


\paper {
  %system-system-spacing #'basic-distance = #15
  %score-system-spacing #'basic-distance = #25
}

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
#(define ((bars-per-line-engraver bar-list) context)
  (let* ((working-copy bar-list)
         (total (1+ (car working-copy))))
    `((acknowledgers
       (paper-column-interface
        . ,(lambda (engraver grob source-engraver)
             (let ((internal-bar (ly:context-property context 'internalBarNumber)))
               (if (and (pair? working-copy)
                        (= (remainder internal-bar total) 0)
                        (eq? #t (ly:grob-property grob 'non-musical)))
                   (begin
                     (set! (ly:grob-property grob 'line-break-permission) 'force)
                     (if (null? (cdr working-copy))
                         (set! working-copy bar-list)
                         (begin
                           (set! working-copy (cdr working-copy))))
                           (set! total (+ total (car working-copy))))))))))))
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

\layout {
  #(layout-set-staff-size 20)
  indent = 0.0\cm 
  ragged-right = ##f
  ragged-last = ##f

  \set Score.proportionalNotationDuration = #(ly:make-moment 1/4)
  \override Score.SpacingSpanner.uniform-stretching = ##t
  \override Score.SpacingSpanner.base-shortest-duration = #(ly:make-moment 1/4) 
  \override Score.SpacingSpanner.common-shortest-duration = #(ly:make-moment 1/4)
  \override Score.SpacingSpanner.shortest-duration-space = #10
  \override Score.RehearsalMark #'self-alignment-X = #LEFT
  \context {
    \Score
    \remove "Bar_number_engraver"
    \override NonMusicalPaperColumn.line-break-permission = ##f
    \consists #(bars-per-line-engraver '(4))
  }

  \set DrumStaff.drumStyleTable = #(alist->hash-table dbdrums)

  \set Timing.beamExceptions = #'()
  \set Timing.baseMoment = #(ly:make-moment 1/4)
  \set Timing.beatStructure = #'(1 1 1 1)
  \set DrumStaff.beamExceptions = #'()
  \set DrumStaff.baseMoment = #(ly:make-moment 1/4)
  \set DrumStaff.beatStructure = #'(1 1 1 1)
  \set Score.beamExceptions = #'()
  \set Score.baseMoment = #(ly:make-moment 1/4)
  \set Score.beatStructure = #'(1 1 1 1)

  %\override DrumStaff.TimeSignature #'space-alist #'first-note = #'(fixed-space . 2)
  %\override DrumStaff.Clef #'space-alist #'first-note = #'(minimum-fixed-space . 3.8)
  \context {
    \DrumStaff
    \numericTimeSignature

    %firstClef = ##f
    %\remove "Clef_engraver"
    %\remove "Time_signature_engraver"
    %\remove "Bar_engraver"
  }

  % REQUIRES drumrests.ly
  \override DrumStaff.RestCollision #'positioning-done = #merge-rests-on-positioning

        %\override Score.LeftEdge #'space-alist #'clef = #'(fixed-space . 10)
        %\override Score.LeftEdge #'space-alist #'first-note = #'(fixed-space . 7)
        %\override Score.Clef #'stencil = #point-stencil
        %\override DrumStaff.SystemStartBrace #'padding = #10
%%         \override DrumStaff.TimeSignature #'space-alist = #'(
%%           (staff-bar extra-space . 0.7)
%%           (first-note fixed-space . 2.0)
%%           (right-edge extra-space . 0.5)
%%           (cue-clef extra-space . 1.5)
%%         )
%%         \override DrumStaff.Clef #'space-alist = #'(
%%           (staff-bar extra-space . 0.7)
%%           (first-note minimum-fixed-space . 3.8)
%%           (right-edge extra-space . 0.5)
%%           (cue-clef extra-space . 1.5)
%%           (key-cancellation minimum-space . 3.5)
%%           (key-signature minimum-space . 3.5)
%%           (time-signature minimum-space . 4.2)
%%           (next-note extra-space . 1.0)
%%         )
}

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%  FUNCTIONS
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%% roundbox: Draw rounded-box around text.
%
#(define-markup-command (roundbox layout props text) (markup?)
  "Draw rounded-box around text."
  (interpret-markup layout props
  #{
    \markup {
      \rounded-box {
        #text
      }
    }
  #}))
%%
%% Usage:
%
%   \markup \roundbox "Struttura A - B - A - C"
%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%% accbox: Genera uno snippet in cui specificare l'accompagnamento
%
%   arg1: fraction as pair - pefinisce il tempo \time
%         eg: 1/4 -> #'(1. 4)
%   arg2: notazione per l'accompagnamento
%         eg: \drmmode {hh16 hh hh hh }
%
#(define accdrums '(
   (hihat   xcircle   #f 0)
))

#(define-markup-command (accbox layout props time accmusic) (pair? ly:music?)
  "doc: TODO"
  (interpret-markup layout props
  #{
  \markup {
    \score {
      \layout { ragged-right = ##t  indent = 0\cm }
      \new DrumStaff \with {
        alignAboveContext = #"3"
        fontSize = #-2
        drumStyleTable = #(alist->hash-table accdrums)
        \override StaffSymbol.staff-space = #(magstep -2)
        \override StaffSymbol.line-count = #1
        \override Stem.Y-extent = ##f
        \override Stem.length = #3
        \remove "Time_signature_engraver"
        \remove "Bar_engraver"
        %\hide Stem
      } <<
        \drummode {
          \time #time
          <<
            \new DrumVoice {
              \override TextScript.padding = #3
              \voiceUP
              #accmusic
            }
          >>
        }
      >>
    }
  }
  #}))
%
%% Usage
%
%   accmusic = \drummode {hh8^"Senso Shuffle" hh}
%   \markup \accbox #'(1 . 4) #accmusic
%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%  VARIABLES
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

% Layout

voiceUP = {
  \voiceOne
  %\override Stem.length = #5
  \override Beam #'positions = #'(5 . 5)
  \override Rest.staff-position = #0
}

voiceDOWN = {
  \voiceTwo
  %\override Stem.length = #-5
  \override Beam #'positions = #'(-5 . -5)
  %\override Rest.staff-position = #0
}

% Sticking

led = _\markup{ \raise #-3.2 "L" }
rid = _\markup{ \raise #-3.2 "R" }

leu = ^\markup{ \raise #4.5 "L" }
riu = ^\markup{ \raise #4.5 "R" }

% Special Notes

flam = \drummode { 
  \override Stem #'length = #4
  \slurDown 
  \acciaccatura{ sn8 } 
  \revert Stem #'length
  \stemUp
}

flamfunc =
#(define-music-function
   (parser location text)
   (markup?)
   (define txt-position
      (if (string=? "R" text)
	-12
	-13
      ))
   #{
     \drummode { 
       \override Stem #'length = #4
       \slurDown 
       \acciaccatura{ 
	 \tweak NoteHead.X-offset #6
	 \tweak Stem.X-offset #6.9
         sn8_\markup{ \halign #txt-position \raise #-3.2 \teeny #text }
       } 
       \revert Stem #'length
       \stemUp
     }
   #}
)

flamrid = \flamfunc "R"
flamled = \flamfunc "L"

drag = \drummode {
  \grace { 
    \override Beam #'positions = #'(2.5 . 2.5) 
    sn8 sn
  }
}

dragfunc =
#(define-music-function
   (parser location text)
   (markup?)
   (define txt-position
      (if (string=? "R" text)
	-12
	-13
      ))
   #{
     \drummode { 
       \slurDown 
       \acciaccatura { 
	 \tweak NoteHead.X-offset #6
	 \tweak Stem.X-offset #6.9
         sn16[_\markup{ \halign #txt-position \raise #-3.2 \teeny #text }
         sn16]_\markup{ \raise #-3.2 \teeny #text }
       } 
       \stemUp
     }
   #}
)

dragrid = \dragfunc "R"
dragled = \dragfunc "L"

\context Score = "DrumScore"
{
    \context DrumStaff = "DrumStaff"
    {
        \drummode {
            <<
                \context DrumVoice = "Symbols"
                {
                    \voiceUP
                    hihat8
                    hihat8
                    hihat8
                    hihat8
                    hihat8
                    hihat8
                    hihat8
                    hihat8
                }
                \context DrumVoice = "DrumVoice"
                {
                    \voiceDOWN
                    bassdrum4
                    <bassdrum snare>4
                    bassdrum4
                    <bassdrum snare>4
                }
            >>
        }
    }
}
