/* eslint-disable @typescript-eslint/no-require-imports */
/* eslint-disable @typescript-eslint/no-explicit-any */
import "whatwg-fetch";
import { TextEncoder, TextDecoder } from "util";
import { TransformStream } from "stream/web";

// Polyfill pentru TextEncoder/TextDecoder
(globalThis as any).TextEncoder = TextEncoder as any;
(globalThis as any).TextDecoder = TextDecoder as any;
(globalThis as any).TransformStream = TransformStream as any;

import "@testing-library/jest-dom";
