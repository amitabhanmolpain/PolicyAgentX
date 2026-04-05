import { Component, type ErrorInfo, type ReactNode } from "react";

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  message: string;
}

export default class SimulateErrorBoundary extends Component<Props, State> {
  state: State = {
    hasError: false,
    message: "",
  };

  static getDerivedStateFromError(error: Error): State {
    return {
      hasError: true,
      message: error?.message || "Unexpected rendering error",
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error("SimulateErrorBoundary caught an error:", error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="rounded-xl border border-red-500/30 bg-red-950/20 p-4">
          <p className="text-[10px] uppercase tracking-[0.14em] text-red-300 font-semibold mb-2">
            Render Error Recovered
          </p>
          <p className="text-sm text-red-100 mb-2">
            Part of the analysis view failed to render, but the app is still running.
          </p>
          <p className="text-xs text-red-200/90">{this.state.message}</p>
        </div>
      );
    }

    return this.props.children;
  }
}
