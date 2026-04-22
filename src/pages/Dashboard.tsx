import { useState, useCallback } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useHealth, useStats, useGoldenRecords, useMatches, runPipeline } from '@/hooks/useApi';
import { StatsCards } from '@/components/dashboard/StatsCards';
import { ConfidenceChart } from '@/components/dashboard/ConfidenceChart';
import { MatchStatusChart } from '@/components/dashboard/MatchStatusChart';
import { PipelineRuns } from '@/components/dashboard/PipelineRuns';
import { QualityTrends } from '@/components/dashboard/QualityTrends';
import { MatchesTable } from '@/components/dashboard/MatchesTable';
import { GoldenRecordsTable } from '@/components/dashboard/GoldenRecordsTable';
import { ResolveForm } from '@/components/dashboard/ResolveForm';
import { LineageView } from '@/components/dashboard/LineageView';

export default function Dashboard() {
  const { data: health, loading: healthLoading } = useHealth();
  const { data: stats, refetch: refetchStats } = useStats();
  const [activeView, setActiveView] = useState('overview');
  const [selectedGoldenId, setSelectedGoldenId] = useState<string | undefined>();
  const [searchQuery, setSearchQuery] = useState('');
  const [isRunning, setIsRunning] = useState(false);

  const { data: goldenData } = useGoldenRecords(searchQuery || undefined);
  const { data: matchesData } = useMatches();

  const handleRunPipeline = useCallback(async () => {
    setIsRunning(true);
    try {
      await runPipeline('all');
      await refetchStats();
    } catch (e) {
      console.error('Pipeline run failed:', e);
    } finally {
      setIsRunning(false);
    }
  }, [refetchStats]);

  const handleSelectGoldenRecord = useCallback((id: string) => {
    setSelectedGoldenId(id);
    setActiveView('lineage');
  }, []);

  const handleBackFromLineage = useCallback(() => {
    setSelectedGoldenId(undefined);
    setActiveView('golden-records');
  }, []);

  if (healthLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="h-8 w-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-muted-foreground">Connecting to GoldenRecord...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b sticky top-0 z-10">
        <div className="max-w-[1600px] mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="h-9 w-9 bg-gradient-to-br from-blue-600 to-indigo-600 rounded-lg flex items-center justify-center">
                <svg className="h-5 w-5 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M12 2L2 7l10 5 10-5-10-5z" />
                  <path d="M2 17l10 5 10-5" />
                  <path d="M2 12l10 5 10-5" />
                </svg>
              </div>
              <div>
                <h1 className="text-lg font-bold tracking-tight">GoldenRecord</h1>
                <p className="text-xs text-muted-foreground">Master Data Reconciliation Platform</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <div className="text-xs text-muted-foreground">
                Database: {health?.database === 'connected' ? (
                  <span className="text-emerald-600 font-medium">Connected</span>
                ) : (
                  <span className="text-red-600 font-medium">Disconnected</span>
                )}
              </div>
              <div className="text-xs text-muted-foreground">
                Status: {health?.status === 'healthy' ? (
                  <span className="text-emerald-600 font-medium">Healthy</span>
                ) : (
                  <span className="text-amber-600 font-medium">Degraded</span>
                )}
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-[1600px] mx-auto px-6 py-6">
        {/* Stats Cards */}
        <div className="mb-6">
          <StatsCards health={health} />
        </div>

        {/* Tabs */}
        <Tabs value={activeView} onValueChange={setActiveView}>
          <TabsList className="mb-6">
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="matches">Matches</TabsTrigger>
            <TabsTrigger value="golden-records">Golden Records</TabsTrigger>
            <TabsTrigger value="resolve">Entity Resolution</TabsTrigger>
            <TabsTrigger value="lineage">Lineage</TabsTrigger>
          </TabsList>

          {/* Overview Tab */}
          <TabsContent value="overview" className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <ConfidenceChart stats={stats} />
              <MatchStatusChart stats={stats} />
            </div>
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <PipelineRuns
                stats={stats}
                onRunPipeline={handleRunPipeline}
                isRunning={isRunning}
              />
              <QualityTrends stats={stats} />
            </div>
          </TabsContent>

          {/* Matches Tab */}
          <TabsContent value="matches" className="space-y-6">
            {matchesData && (
              <MatchesTable matches={matchesData.matches || []} />
            )}
          </TabsContent>

          {/* Golden Records Tab */}
          <TabsContent value="golden-records" className="space-y-6">
            {goldenData && (
              <GoldenRecordsTable
                records={goldenData.records || []}
                onSelectRecord={handleSelectGoldenRecord}
                searchQuery={searchQuery}
                onSearchChange={setSearchQuery}
              />
            )}
          </TabsContent>

          {/* Resolve Tab */}
          <TabsContent value="resolve" className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <ResolveForm />
              <div className="lg:col-span-2">
                <div className="p-6 bg-white rounded-lg border">
                  <h3 className="text-base font-semibold mb-4">How Entity Resolution Works</h3>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="p-4 bg-blue-50 rounded-lg">
                      <div className="text-blue-600 font-bold text-lg mb-2">1. Standardize</div>
                      <p className="text-sm text-muted-foreground">
                        Parse and normalize names, emails, phones, and company names into canonical forms.
                      </p>
                    </div>
                    <div className="p-4 bg-indigo-50 rounded-lg">
                      <div className="text-indigo-600 font-bold text-lg mb-2">2. Block & Score</div>
                      <p className="text-sm text-muted-foreground">
                        Multi-index blocking reduces comparisons. Weighted features compute confidence scores.
                      </p>
                    </div>
                    <div className="p-4 bg-emerald-50 rounded-lg">
                      <div className="text-emerald-600 font-bold text-lg mb-2">3. Merge</div>
                      <p className="text-sm text-muted-foreground">
                        Survivorship rules select the best values. Full audit trail captures every decision.
                      </p>
                    </div>
                  </div>

                  <div className="mt-6">
                    <h4 className="text-sm font-semibold mb-3">Confidence Thresholds</h4>
                    <div className="space-y-2">
                      <div className="flex items-center gap-3">
                        <div className="w-3 h-3 rounded-full bg-emerald-500" />
                        <span className="text-sm font-medium w-32">Auto Merge</span>
                        <span className="text-sm text-muted-foreground">Confidence &ge; 0.85 - Automatically merge records</span>
                      </div>
                      <div className="flex items-center gap-3">
                        <div className="w-3 h-3 rounded-full bg-amber-500" />
                        <span className="text-sm font-medium w-32">Review Queue</span>
                        <span className="text-sm text-muted-foreground">Confidence 0.60-0.85 - Requires manual review</span>
                      </div>
                      <div className="flex items-center gap-3">
                        <div className="w-3 h-3 rounded-full bg-gray-400" />
                        <span className="text-sm font-medium w-32">Distinct</span>
                        <span className="text-sm text-muted-foreground">Confidence &lt; 0.60 - Records are distinct</span>
                      </div>
                    </div>
                  </div>

                  <div className="mt-6">
                    <h4 className="text-sm font-semibold mb-3">Feature Weights</h4>
                    <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
                      {[
                        { name: 'Email Exact', weight: 0.35, color: 'bg-blue-500' },
                        { name: 'Phone Exact', weight: 0.25, color: 'bg-indigo-500' },
                        { name: 'Name Similarity', weight: 0.20, color: 'bg-violet-500' },
                        { name: 'Email Domain', weight: 0.10, color: 'bg-purple-500' },
                        { name: 'Company Match', weight: 0.10, color: 'bg-fuchsia-500' },
                      ].map((f) => (
                        <div key={f.name} className="p-3 bg-muted/50 rounded-lg text-center">
                          <div className={`h-2 w-full ${f.color} rounded-full mb-2`} />
                          <div className="text-xs font-medium">{f.name}</div>
                          <div className="text-xs text-muted-foreground">{f.weight}</div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </TabsContent>

          {/* Lineage Tab */}
          <TabsContent value="lineage" className="space-y-6">
            <LineageView
              goldenId={selectedGoldenId}
              onBack={handleBackFromLineage}
            />
          </TabsContent>
        </Tabs>
      </main>
    </div>
  );
}
