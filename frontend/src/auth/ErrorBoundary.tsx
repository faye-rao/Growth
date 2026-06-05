import React from "react";
import { Result, Button } from "antd";

interface State {
  error: Error | null;
}

// App-wide error boundary: prevents a render error in one screen from blanking
// the whole console; shows a recoverable Result.
export default class ErrorBoundary extends React.Component<
  { children: React.ReactNode },
  State
> {
  state: State = { error: null };

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  render() {
    if (this.state.error) {
      return (
        <Result
          status="error"
          title="Something went wrong"
          subTitle={this.state.error.message}
          extra={
            <Button type="primary" onClick={() => this.setState({ error: null })}>
              Try again
            </Button>
          }
        />
      );
    }
    return this.props.children;
  }
}
