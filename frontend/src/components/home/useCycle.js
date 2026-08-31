import { useEffect, useState } from "react";
import { useInView, useReducedMotion } from "motion/react";

export function useCycle(length, ms, ref) {
  const reduceMotion = useReducedMotion();
  const inView = useInView(ref, { amount: 0.2, once: false });
  const [index, setIndex] = useState(0);
  const [paused, setPaused] = useState(false);

  useEffect(() => {
    const node = ref.current;
    if (!node) return undefined;

    const pause = () => setPaused(true);
    const resume = (event) => {
      if (event.type === "focusout" && node.contains(event.relatedTarget)) {
        return;
      }
      setPaused(false);
    };

    node.addEventListener("pointerenter", pause);
    node.addEventListener("pointerleave", resume);
    node.addEventListener("focusin", pause);
    node.addEventListener("focusout", resume);

    return () => {
      node.removeEventListener("pointerenter", pause);
      node.removeEventListener("pointerleave", resume);
      node.removeEventListener("focusin", pause);
      node.removeEventListener("focusout", resume);
    };
  }, [ref]);

  useEffect(() => {
    if (reduceMotion || !inView || paused || length < 2) {
      return undefined;
    }

    const interval =
      typeof window !== "undefined" &&
      window.matchMedia("(max-width: 768px)").matches
        ? ms + 800
        : ms;

    const timer = window.setInterval(() => {
      setIndex((value) => (value + 1) % length);
    }, interval);

    return () => window.clearInterval(timer);
  }, [reduceMotion, inView, paused, length, ms]);

  return [index, setIndex];
}
