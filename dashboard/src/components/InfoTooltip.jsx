import React, { useState, useRef, useEffect } from 'react';
import { createPortal } from 'react-dom';
import { HelpCircle, Sparkles, X, Lightbulb } from 'lucide-react';
import { getGlossaryTerm } from '../data/glossary';

/**
 * InfoTooltip provides plain-English descriptions for any financial / CSE technical term.
 *
 * Uses React Portal and smart viewport clamping so tooltips NEVER get cut off or go outside the browser window.
 */
export default function InfoTooltip({
  termId,
  title,
  text,
  example,
  children,
  size = 'sm',
}) {
  const [isOpen, setIsOpen] = useState(false);
  const [coords, setCoords] = useState(null);
  const triggerRef = useRef(null);
  const tooltipRef = useRef(null);
  const closeTimeoutRef = useRef(null);

  const termData = termId ? getGlossaryTerm(termId) : null;
  const displayTitle = title || termData?.term || termId || 'Stock Term';
  const displaySimple = text || termData?.simple || 'Financial metric used in stock analysis.';
  const displayDetails = termData?.details;
  const displayExample = example || termData?.example;

  const updatePosition = () => {
    if (!triggerRef.current) return;
    const rect = triggerRef.current.getBoundingClientRect();
    const tooltipWidth = Math.min(300, window.innerWidth - 24);

    // Check vertical space (flip below if close to window top)
    const spaceAbove = rect.top;
    const spaceBelow = window.innerHeight - rect.bottom;
    const placeBelow = spaceAbove < 230 && spaceBelow >= spaceAbove;

    // Horizontal clamping to prevent left/right screen overflow
    const idealLeft = rect.left + rect.width / 2 - tooltipWidth / 2;
    const clampedLeft = Math.max(12, Math.min(idealLeft, window.innerWidth - tooltipWidth - 12));

    // Arrow pointer position relative to tooltip box (points at trigger center)
    const arrowLeft = Math.max(16, Math.min(rect.left + rect.width / 2 - clampedLeft, tooltipWidth - 16));

    setCoords({
      top: placeBelow ? rect.bottom + 8 : undefined,
      bottom: !placeBelow ? window.innerHeight - rect.top + 8 : undefined,
      left: clampedLeft,
      width: tooltipWidth,
      placeBelow,
      arrowLeft,
    });
  };

  useEffect(() => {
    if (!isOpen) return;

    updatePosition();

    const handleScrollOrResize = () => {
      updatePosition();
    };

    const handleClickOutside = (e) => {
      if (
        triggerRef.current &&
        !triggerRef.current.contains(e.target) &&
        tooltipRef.current &&
        !tooltipRef.current.contains(e.target)
      ) {
        setIsOpen(false);
      }
    };

    const handleKeyDown = (e) => {
      if (e.key === 'Escape') {
        setIsOpen(false);
      }
    };

    window.addEventListener('scroll', handleScrollOrResize, true);
    window.addEventListener('resize', handleScrollOrResize);
    document.addEventListener('mousedown', handleClickOutside);
    document.addEventListener('keydown', handleKeyDown);

    return () => {
      window.removeEventListener('scroll', handleScrollOrResize, true);
      window.removeEventListener('resize', handleScrollOrResize);
      document.removeEventListener('mousedown', handleClickOutside);
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [isOpen]);

  const handleMouseEnter = () => {
    if (closeTimeoutRef.current) {
      clearTimeout(closeTimeoutRef.current);
      closeTimeoutRef.current = null;
    }
    setIsOpen(true);
  };

  const handleMouseLeave = () => {
    closeTimeoutRef.current = setTimeout(() => {
      setIsOpen(false);
    }, 180);
  };

  const toggleTooltip = (e) => {
    e.stopPropagation();
    e.preventDefault();
    setIsOpen((prev) => !prev);
  };

  return (
    <>
      <span
        ref={triggerRef}
        className="relative inline-flex items-center gap-1 group/tooltip cursor-help select-none"
        onMouseEnter={handleMouseEnter}
        onMouseLeave={handleMouseLeave}
      >
        {children ? (
          <span className="border-b border-dotted border-blue-400/70 hover:border-blue-400 hover:text-blue-300 transition-colors">
            {children}
          </span>
        ) : null}

        <button
          type="button"
          onClick={toggleTooltip}
          aria-label={`What is ${displayTitle}?`}
          className={`inline-flex items-center justify-center rounded-full text-slate-400 hover:text-blue-400 hover:bg-blue-500/10 transition-colors ${
            size === 'xs' ? 'w-3.5 h-3.5 text-[10px]' : 'w-4 h-4 text-xs'
          }`}
        >
          <HelpCircle className="w-3.5 h-3.5" />
        </button>
      </span>

      {/* Floating Tooltip via Portal with Viewport Clamping */}
      {isOpen && coords && typeof document !== 'undefined'
        ? createPortal(
            <div
              ref={tooltipRef}
              role="tooltip"
              onMouseEnter={handleMouseEnter}
              onMouseLeave={handleMouseLeave}
              style={{
                position: 'fixed',
                top: coords.top !== undefined ? `${coords.top}px` : undefined,
                bottom: coords.bottom !== undefined ? `${coords.bottom}px` : undefined,
                left: `${coords.left}px`,
                width: `${coords.width}px`,
                zIndex: 99999,
              }}
              className="p-3.5 bg-slate-900/95 backdrop-blur-md border border-blue-500/40 rounded-xl shadow-2xl text-left text-xs text-slate-200 pointer-events-auto animate-in fade-in zoom-in-95 duration-150"
            >
              {/* Header */}
              <div className="flex items-start justify-between gap-2 pb-2 border-b border-slate-800">
                <div className="flex items-center gap-1.5 font-bold text-white">
                  <Sparkles className="w-3.5 h-3.5 text-amber-400 shrink-0" />
                  <span className="line-clamp-1">{displayTitle}</span>
                </div>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    setIsOpen(false);
                  }}
                  className="text-slate-400 hover:text-white rounded p-0.5 transition"
                  title="Close"
                >
                  <X className="w-3.5 h-3.5" />
                </button>
              </div>

              {/* Simple Explanation */}
              <div className="mt-2 text-slate-100 leading-relaxed font-medium">
                {displaySimple}
              </div>

              {/* Expanded Details */}
              {displayDetails && (
                <p className="mt-1.5 text-slate-400 text-[11px] leading-relaxed">
                  {displayDetails}
                </p>
              )}

              {/* Example Box */}
              {displayExample && (
                <div className="mt-2.5 p-2 bg-slate-950/90 rounded border border-slate-800 text-[11px]">
                  <span className="text-amber-400 font-semibold flex items-center gap-1 text-[10px] uppercase tracking-wider">
                    <Lightbulb className="w-3 h-3 text-amber-400" />
                    <span>Real Example:</span>
                  </span>
                  <span className="text-slate-300 mt-0.5 block leading-normal">{displayExample}</span>
                </div>
              )}

              {/* Dynamic Arrow */}
              {coords.placeBelow ? (
                <div
                  style={{ left: `${coords.arrowLeft}px` }}
                  className="absolute bottom-full -mb-px -translate-x-1/2 border-4 border-transparent border-b-slate-900"
                />
              ) : (
                <div
                  style={{ left: `${coords.arrowLeft}px` }}
                  className="absolute top-full -mt-px -translate-x-1/2 border-4 border-transparent border-t-slate-900"
                />
              )}
            </div>,
            document.body
          )
        : null}
    </>
  );
}
