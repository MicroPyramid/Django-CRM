import { getContext, setContext, } from "svelte";

export const THEMES = { light: "", dark: ".dark" } ;

// Helper to extract item config from a payload.
export function getPayloadConfigFromPayload(
	config,
	payload,
	key
) {
	if (typeof payload !== "object" || payload === null) return undefined;

	const payloadPayload =
		"payload" in payload && typeof payload.payload === "object" && payload.payload !== null
			? payload.payload
			: undefined;

	let configLabelKey = key;

	if (payload.key === key) {
		configLabelKey = payload.key;
	} else if (payload.name === key) {
		configLabelKey = payload.name;
	} else if (key in payload && typeof payload[key ] === "string") {
		configLabelKey = payload[key ] ;
	} else if (
		payloadPayload !== undefined &&
		key in payloadPayload &&
		typeof payloadPayload[key ] === "string"
	) {
		configLabelKey = payloadPayload[key ] ;
	}

	return configLabelKey in config ? config[configLabelKey] : config[key ];
}

const chartContextKey = Symbol("chart-context");

export function setChartContext(value) {
	return setContext(chartContextKey, value);
}

export function useChart() {
	return getContext(chartContextKey);
}