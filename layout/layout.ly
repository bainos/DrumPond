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
