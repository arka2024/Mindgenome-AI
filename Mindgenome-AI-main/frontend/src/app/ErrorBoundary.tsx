import { Component, type ErrorInfo, type ReactNode } from "react";
import { Button } from "@/shared/ui/Button";

type Props = { children: ReactNode };
type State = { error: Error | null };

export class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null };

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  componentDidCatch(error: Error, info: ErrorInfo): void {
    console.error(error, info);
  }

  render() {
    if (this.state.error) {
      return (
        <div className="mx-auto max-w-lg p-8 text-center">
          <h1 className="font-display text-3xl">Something snapped in the helix</h1>
          <p className="mt-2 text-muted">The last screen hit an unexpected error. Your data is still on the server.</p>
          <Button className="mt-4" onClick={() => this.setState({ error: null })}>
            Try again
          </Button>
        </div>
      );
    }
    return this.props.children;
  }
}
