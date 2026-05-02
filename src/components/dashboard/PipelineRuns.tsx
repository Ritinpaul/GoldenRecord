import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Clock, CheckCircle, XCircle, Play, RotateCw } from 'lucide-react';
import { Button } from '@/components/ui/button';
import type { StatsResponse } from '@/types';

interface PipelineRunsProps {
  stats: StatsResponse | null;
  onRunPipeline: () => void;
  isRunning: boolean;
}

function getStatusBadge(status: string) {
  if (status === 'completed') return <Badge className="bg-emerald-100 text-emerald-700 hover:bg-emerald-200">Completed</Badge>;
  if (status === 'running') return <Badge className="bg-blue-100 text-blue-700 hover:bg-blue-200">Running</Badge>;
  if (status.startsWith('failed')) return <Badge className="bg-red-100 text-red-700 hover:bg-red-200">Failed</Badge>;
  return <Badge variant="secondary">{status}</Badge>;
}

function getStatusIcon(status: string) {
  if (status === 'completed') return <CheckCircle className="h-4 w-4 text-emerald-500" />;
  if (status === 'running') return <RotateCw className="h-4 w-4 text-blue-500 animate-spin" />;
  if (status.startsWith('failed')) return <XCircle className="h-4 w-4 text-red-500" />;
  return <Clock className="h-4 w-4 text-gray-400" />;
}

export function PipelineRuns({ stats, onRunPipeline, isRunning }: PipelineRunsProps) {
  const runs = stats?.recent_runs || [];

  return (
    <Card className="col-span-1">
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle className="text-base font-semibold">Reconciliation Runs</CardTitle>
        <Button
          size="sm"
          onClick={onRunPipeline}
          disabled={isRunning}
          className="bg-blue-600 hover:bg-blue-700"
        >
          {isRunning ? (
            <RotateCw className="h-4 w-4 mr-1 animate-spin" />
          ) : (
            <Play className="h-4 w-4 mr-1" />
          )}
          {isRunning ? 'Running...' : 'Run Pipeline'}
        </Button>
      </CardHeader>
      <CardContent>
        {runs.length > 0 ? (
          <div className="space-y-3 max-h-[280px] overflow-y-auto pr-1">
            {runs.map((run) => (
              <div
                key={run.run_id}
                className="flex items-start gap-3 p-3 rounded-lg bg-muted/50 hover:bg-muted transition-colors"
              >
                <div className="mt-0.5">{getStatusIcon(run.status)}</div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-mono text-muted-foreground truncate">
                      {run.run_id}
                    </span>
                    {getStatusBadge(run.status)}
                  </div>
                  <div className="flex items-center gap-3 mt-1 text-xs text-muted-foreground">
                    <span>{run.source_system}</span>
                    <span>{(run.records_in || 0).toLocaleString()} records</span>
                    {run.run_duration_ms && (
                      <span>{(run.run_duration_ms / 1000).toFixed(1)}s</span>
                    )}
                  </div>
                  <div className="text-xs text-muted-foreground mt-0.5">
                    {new Date(run.run_timestamp).toLocaleString()}
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="flex items-center justify-center h-[200px]">
            <p className="text-muted-foreground text-sm">No runs yet</p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
