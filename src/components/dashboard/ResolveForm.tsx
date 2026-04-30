import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Search, Loader2, CheckCircle, AlertTriangle } from 'lucide-react';
import { resolveRecord } from '@/hooks/useApi';
import type { ResolveResponse } from '@/types';

export function ResolveForm() {
  const [form, setForm] = useState({
    email: '',
    first_name: '',
    last_name: '',
    company_name: '',
    phone: '',
    region: '',
  });
  const [result, setResult] = useState<ResolveResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const data = await resolveRecord({
        email: form.email || undefined,
        first_name: form.first_name || undefined,
        last_name: form.last_name || undefined,
        company_name: form.company_name || undefined,
        phone: form.phone || undefined,
        region: form.region || undefined,
      });
      setResult(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Resolution failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card className="col-span-1">
      <CardHeader>
        <CardTitle className="text-base font-semibold">Entity Resolution</CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-3">
          <Input
            placeholder="Email"
            value={form.email}
            onChange={(e) => setForm({ ...form, email: e.target.value })}
            className="text-sm"
          />
          <div className="grid grid-cols-2 gap-2">
            <Input
              placeholder="First Name"
              value={form.first_name}
              onChange={(e) => setForm({ ...form, first_name: e.target.value })}
              className="text-sm"
            />
            <Input
              placeholder="Last Name"
              value={form.last_name}
              onChange={(e) => setForm({ ...form, last_name: e.target.value })}
              className="text-sm"
            />
          </div>
          <Input
            placeholder="Company"
            value={form.company_name}
            onChange={(e) => setForm({ ...form, company_name: e.target.value })}
            className="text-sm"
          />
          <Input
            placeholder="Phone"
            value={form.phone}
            onChange={(e) => setForm({ ...form, phone: e.target.value })}
            className="text-sm"
          />
          <Input
            placeholder="Region"
            value={form.region}
            onChange={(e) => setForm({ ...form, region: e.target.value })}
            className="text-sm"
          />
          <Button
            type="submit"
            disabled={loading}
            className="w-full bg-blue-600 hover:bg-blue-700"
          >
            {loading ? (
              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
            ) : (
              <Search className="h-4 w-4 mr-2" />
            )}
            {loading ? 'Resolving...' : 'Find Matches'}
          </Button>
        </form>

        {error && (
          <div className="mt-4 p-3 bg-red-50 rounded-lg text-sm text-red-600 flex items-center gap-2">
            <AlertTriangle className="h-4 w-4" />
            {error}
          </div>
        )}

        {result && (
          <div className="mt-4 space-y-3">
            {result.best_match ? (
              <div className="p-3 bg-emerald-50 rounded-lg">
                <div className="flex items-center gap-2 mb-2">
                  <CheckCircle className="h-4 w-4 text-emerald-600" />
                  <span className="font-semibold text-sm text-emerald-800">
                    Best Match Found
                  </span>
                </div>
                <div className="space-y-1 text-sm">
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Confidence:</span>
                    <Badge
                      className={
                        result.best_match.confidence >= 0.85
                          ? 'bg-emerald-100 text-emerald-700'
                          : result.best_match.confidence >= 0.6
                          ? 'bg-amber-100 text-amber-700'
                          : 'bg-gray-100 text-gray-700'
                      }
                    >
                      {(result.best_match.confidence * 100).toFixed(1)}%
                    </Badge>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Status:</span>
                    <Badge variant="outline">{result.best_match.status}</Badge>
                  </div>
                  {result.best_match.golden_record_id && (
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Golden Record:</span>
                      <span className="font-mono text-xs">{result.best_match.golden_record_id}</span>
                    </div>
                  )}
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Source:</span>
                    <span>{result.best_match.source_system}</span>
                  </div>
                </div>

                {result.best_match.explanation && (
                  <div className="mt-2 pt-2 border-t border-emerald-200">
                    <div className="text-xs text-emerald-700 font-medium mb-1">Top Factors:</div>
                    {(result.best_match.explanation.top_factors as Array<{feature: string; value: number; contribution: number}>)?.map((factor) => (
                      <div key={factor.feature} className="flex justify-between text-xs">
                        <span className="text-muted-foreground">{factor.feature}:</span>
                        <span>{factor.value.toFixed(3)} (w: {factor.contribution.toFixed(3)})</span>
                      </div>
                    )) || (
                      <div className="text-xs text-muted-foreground">No factors available</div>
                    )}
                  </div>
                )}
              </div>
            ) : (
              <div className="p-3 bg-gray-50 rounded-lg text-sm text-muted-foreground">
                No matches found for this record
              </div>
            )}

            {result.total_matches_found > 0 && (
              <div className="text-xs text-muted-foreground text-center">
                {result.total_matches_found} total match{result.total_matches_found !== 1 ? 'es' : ''} found
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
