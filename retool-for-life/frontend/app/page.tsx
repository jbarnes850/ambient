'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useWebSocket } from '@/hooks/useWebSocket';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Brain, 
  Heart, 
  Activity, 
  Moon, 
  MessageSquare, 
  Calendar,
  Package,
  ChevronRight,
  CheckCircle,
  XCircle,
  Clock
} from 'lucide-react';

interface AgentAction {
  timestamp: string;
  action: string;
  status: string;
  output: any;
  tool_calls?: any[];
}

interface AgentStatus {
  agent: {
    name: string;
    type: string;
    model: string;
    version: number;
  };
  recent_actions: AgentAction[];
  performance: Record<string, number>;
}

interface User {
  id: string;
  name: string;
  wellness_goals: string[];
  preferences?: {
    messaging_channel?: string;
  };
}

export default function Dashboard() {
  const [users, setUsers] = useState<User[]>([]);
  const [selectedUser, setSelectedUser] = useState<User | null>(null);
  const [agentStatus, setAgentStatus] = useState<AgentStatus | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [isDemoRunning, setIsDemoRunning] = useState(false);
  const [demoResults, setDemoResults] = useState<any[]>([]);
  const [pendingApprovals, setPendingApprovals] = useState<any[]>([]);
  const [evaluationTraces, setEvaluationTraces] = useState<any>(null);
  
  const { messages, isConnected } = useWebSocket(
    selectedUser ? `ws://localhost:8000/ws/${selectedUser.id}` : null
  );

  // Fetch users on mount
  useEffect(() => {
    fetchUsers();
  }, []);

  // Fetch pending approvals periodically
  useEffect(() => {
    const interval = setInterval(fetchPendingApprovals, 2000);
    return () => clearInterval(interval);
  }, []);

  // Handle WebSocket messages for evaluation traces
  useEffect(() => {
    const latestMessage = messages[messages.length - 1];
    if (latestMessage?.type === 'agent_generation' && latestMessage?.evaluation_traces) {
      setEvaluationTraces(latestMessage.evaluation_traces);
    }
  }, [messages]);

  const fetchUsers = async () => {
    try {
      const response = await fetch('/api/users');
      const data = await response.json();
      setUsers(data.users);
      if (data.users.length > 0) {
        setSelectedUser(data.users[0]);
      }
    } catch (error) {
      console.error('Failed to fetch users:', error);
    }
  };

  const fetchPendingApprovals = async () => {
    try {
      const response = await fetch('/api/approvals/pending');
      const data = await response.json();
      setPendingApprovals(data);
    } catch (error) {
      console.error('Failed to fetch approvals:', error);
    }
  };

  const generateAgent = async () => {
    if (!selectedUser) return;
    
    setIsGenerating(true);
    try {
      const response = await fetch(
        `/api/users/${selectedUser.id}/generate-agent`,
        { method: 'POST' }
      );
      const data = await response.json();
      
      // Poll for status
      setTimeout(() => fetchAgentStatus(), 2000);
    } catch (error) {
      console.error('Failed to generate agent:', error);
    } finally {
      setIsGenerating(false);
    }
  };

  const fetchAgentStatus = async () => {
    if (!selectedUser) return;
    
    try {
      const response = await fetch(`/api/users/${selectedUser.id}/agent-status`);
      if (response.ok) {
        const data = await response.json();
        setAgentStatus(data);
      } else if (response.status === 404) {
        // No agent generated yet - this is normal
        setAgentStatus(null);
      }
    } catch (error) {
      console.error('Failed to fetch status:', error);
    }
  };

  const runDemo = async () => {
    if (!selectedUser) return;
    
    setIsDemoRunning(true);
    setDemoResults([]);
    
    try {
      const response = await fetch(
        `/api/users/${selectedUser.id}/trigger-demo`,
        { method: 'POST' }
      );
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      setDemoResults(data.demo_results || []);
      
      // Refresh status after demo
      setTimeout(() => fetchAgentStatus(), 1000);
    } catch (error) {
      console.error('Failed to run demo:', error);
      setDemoResults([]);
    } finally {
      setIsDemoRunning(false);
    }
  };

  const approveAction = async (approvalId: string) => {
    try {
      await fetch(`/api/approvals/${approvalId}/approve`, { method: 'POST' });
      await fetchPendingApprovals();
    } catch (error) {
      console.error('Failed to approve action:', error);
    }
  };

  useEffect(() => {
    if (selectedUser) {
      fetchAgentStatus();
      const interval = setInterval(fetchAgentStatus, 10000);
      return () => clearInterval(interval);
    }
  }, [selectedUser]);

  const getGoalIcon = (goal: string) => {
    if (goal.includes('sleep')) return <Moon className="w-4 h-4" />;
    if (goal.includes('stress')) return <Brain className="w-4 h-4" />;
    if (goal.includes('exercise') || goal.includes('fitness')) return <Activity className="w-4 h-4" />;
    if (goal.includes('hydration') || goal.includes('nutrition')) return <Heart className="w-4 h-4" />;
    return <Heart className="w-4 h-4" />;
  };

  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto p-4 space-y-4">
        <header className="flex justify-between items-center mb-6">
          <div>
            <h1 className="text-3xl font-bold">Ambient</h1>
            <p className="text-muted-foreground">Personalized wellness agent platform</p>
          </div>
          <div className="flex items-center gap-2">
            <Badge variant={isConnected ? 'default' : 'secondary'}>
              {isConnected ? 'Connected' : 'Disconnected'}
            </Badge>
            {agentStatus && (
              <Badge variant="outline">
                v{agentStatus.agent.version}
              </Badge>
            )}
          </div>
        </header>

        {/* Info Section */}
        {!agentStatus && (
          <div className="mb-6 p-4 bg-primary/5 border border-primary/20 rounded-lg">
            <div className="flex items-center gap-2 mb-2">
              <Brain className="w-5 h-5 text-primary" />
              <h2 className="text-lg font-semibold">System Overview</h2>
            </div>
            <p className="text-sm text-muted-foreground">
              The system automatically generates, evaluates, and deploys personalized agents based on user profiles.
              Performance metrics are tracked and optimized through machine learning feedback loops.
            </p>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          {/* User Selection & Setup Panel */}
          <Card>
            <CardHeader>
              <CardTitle>Agent Configuration</CardTitle>
              <CardDescription>Select user profile and initialize agent</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* User Selection */}
              <div className="space-y-2">
                <label className="text-sm font-medium">Select User</label>
                <div className="space-y-2">
                  {users.map((user) => (
                    <button
                      key={user.id}
                      onClick={() => setSelectedUser(user)}
                      className={`w-full p-3 rounded-lg border text-left transition-colors ${
                        selectedUser?.id === user.id 
                          ? 'border-primary bg-primary/5' 
                          : 'border-border hover:border-primary/50'
                      }`}
                    >
                      <div className="font-medium">{user.name}</div>
                      <div className="flex gap-2 mt-1">
                        {user.wellness_goals.map((goal) => (
                          <div key={goal} className="flex items-center gap-1">
                            {getGoalIcon(goal)}
                            <span className="text-xs text-muted-foreground">{goal}</span>
                          </div>
                        ))}
                      </div>
                      <div className="text-xs text-muted-foreground mt-1">
                        Prefers: {user.preferences?.messaging_channel || 'SMS'}
                      </div>
                    </button>
                  ))}
                </div>
              </div>
              
              {/* Connection Status */}
              <div className="space-y-2">
                <ConnectionStatus service="Health Data" connected={true} icon={<Heart className="w-4 h-4" />} />
                <ConnectionStatus service="Calendar" connected={true} icon={<Calendar className="w-4 h-4" />} />
                <ConnectionStatus service="SMS/WhatsApp" connected={true} icon={<MessageSquare className="w-4 h-4" />} />
                <ConnectionStatus service="Commerce" connected={true} icon={<Package className="w-4 h-4" />} />
              </div>
              
              {/* Action Buttons */}
              <div className="space-y-2">
                <Button
                  onClick={generateAgent}
                  disabled={!selectedUser || isGenerating || !!agentStatus}
                  className="w-full"
                  size="lg"
                >
                  {isGenerating ? (
                    <>Generating agent...</>
                  ) : agentStatus ? (
                    <>Agent Active: {agentStatus.agent.type}</>
                  ) : (
                    <>Generate Agent</>
                  )}
                </Button>
                
                {agentStatus && (
                  <Button 
                    onClick={runDemo} 
                    variant="outline" 
                    className="w-full"
                    size="lg"
                    disabled={isDemoRunning}
                  >
                    {isDemoRunning ? 'Running demo sequence...' : 'Run Demo Sequence'}
                  </Button>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Live Actions & Approvals */}
          <Card>
            <CardHeader>
              <CardTitle>Agent Activity</CardTitle>
              <CardDescription>Real-time monitoring and approval system</CardDescription>
            </CardHeader>
            <CardContent>
              <Tabs defaultValue="actions">
                <TabsList className="grid w-full grid-cols-2">
                  <TabsTrigger value="actions">Actions</TabsTrigger>
                  <TabsTrigger value="approvals">
                    Approvals {pendingApprovals.length > 0 && (
                      <Badge className="ml-2" variant="destructive">{pendingApprovals.length}</Badge>
                    )}
                  </TabsTrigger>
                </TabsList>
                
                <TabsContent value="actions" className="space-y-2 mt-4">
                  <AnimatePresence mode="popLayout">
                    {messages.slice(-5).reverse().map((msg, idx) => (
                      <motion.div
                        key={idx}
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        exit={{ opacity: 0, x: 20 }}
                        className="p-3 bg-secondary rounded-lg"
                      >
                        <ActionDisplay action={msg} />
                      </motion.div>
                    ))}
                  </AnimatePresence>
                  
                  {demoResults && demoResults.length > 0 && (
                    <div className="mt-4 space-y-2">
                      <h4 className="text-sm font-medium">Demo Results</h4>
                      {demoResults.map((result, idx) => (
                        <div
                          key={idx}
                          className="p-3 bg-secondary rounded-lg space-y-1"
                        >
                          <div className="flex justify-between items-center">
                            <span className="font-medium text-sm">{result.time}</span>
                            <Badge variant={result.status === 'completed' ? 'default' : 'secondary'}>
                              {result.description}
                            </Badge>
                          </div>
                          {result.response && (
                            <p className="text-sm text-muted-foreground">
                              {result.response.message}
                            </p>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </TabsContent>
                
                <TabsContent value="approvals" className="space-y-2 mt-4">
                  {pendingApprovals.length === 0 ? (
                    <p className="text-center text-muted-foreground py-8">No pending approvals</p>
                  ) : (
                    pendingApprovals.map((approval) => (
                      <div key={approval.approval_id} className="p-4 border rounded-lg space-y-3">
                        <div className="flex items-start justify-between">
                          <div className="space-y-1">
                            <Badge variant="outline">{approval.type}</Badge>
                            <p className="text-sm font-medium">{approval.message}</p>
                            <p className="text-xs text-muted-foreground">
                              To: {approval.to_number}
                            </p>
                          </div>
                        </div>
                        <Button
                          size="sm"
                          onClick={() => approveAction(approval.approval_id)}
                          className="w-full"
                        >
                          Approve & Send
                        </Button>
                      </div>
                    ))
                  )}
                </TabsContent>
              </Tabs>
            </CardContent>
          </Card>

          {/* Performance & Observability */}
          <Card>
            <CardHeader>
              <CardTitle>Performance Metrics</CardTitle>
              <CardDescription>System optimization and performance tracking</CardDescription>
            </CardHeader>
            <CardContent>
              <Tabs defaultValue="metrics">
                <TabsList className="grid w-full grid-cols-2">
                  <TabsTrigger value="metrics">Performance</TabsTrigger>
                  <TabsTrigger value="traces">
                    Evaluation {evaluationTraces && (
                      <Badge className="ml-2" variant="outline">New</Badge>
                    )}
                  </TabsTrigger>
                </TabsList>
                
                <TabsContent value="metrics" className="space-y-4">
              {agentStatus?.performance && (
                <div className="space-y-3">
                  {Object.entries(agentStatus.performance).map(([key, value]) => (
                    <div key={key} className="space-y-1">
                      <div className="flex justify-between text-sm">
                        <span className="capitalize">
                          {key.replace(/_/g, ' ')}
                        </span>
                        <span className="font-medium">{(value * 100).toFixed(0)}%</span>
                      </div>
                      <Progress value={value * 100} />
                    </div>
                  ))}
                </div>
              )}
              
              <div className="pt-4">
                <h4 className="text-sm font-medium mb-2">Recent Actions</h4>
                <div className="space-y-2">
                  {agentStatus?.recent_actions.slice(0, 5).map((action, idx) => (
                    <div
                      key={idx}
                      className="text-xs space-y-1 p-2 bg-secondary rounded"
                    >
                      <div className="flex justify-between">
                        <span className="font-medium">{action.action}</span>
                        <Badge
                          variant={
                            action.status === 'completed' ? 'default' : 'secondary'
                          }
                          className="text-xs"
                        >
                          {action.status}
                        </Badge>
                      </div>
                      <p className="text-muted-foreground">
                        {new Date(action.timestamp).toLocaleTimeString()}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
                </TabsContent>
                
                <TabsContent value="traces" className="space-y-2">
                  {evaluationTraces ? (
                    <div className="space-y-3">
                      <h4 className="text-sm font-medium">Agent Evaluation Results</h4>
                      {Object.entries(evaluationTraces).map(([agentName, traces]: [string, any]) => (
                        <div key={agentName} className="space-y-2">
                          <div className="flex items-center justify-between">
                            <span className="text-sm font-medium">{agentName}</span>
                            <Badge variant="outline">
                              Score: {traces.reduce((acc: number, t: any) => acc + (t.score || 0), 0) / traces.length * 100}%
                            </Badge>
                          </div>
                          <div className="space-y-1">
                            {traces.map((trace: any, idx: number) => (
                              <div key={idx} className="text-xs p-2 bg-secondary rounded">
                                <div className="flex justify-between items-center mb-1">
                                  <span className="font-medium">{trace.scenario}</span>
                                  <Badge variant={trace.score >= 0.8 ? 'default' : 'secondary'} className="text-xs">
                                    {(trace.score * 100).toFixed(0)}%
                                  </Badge>
                                </div>
                                {trace.trace_data && (
                                  <p className="text-muted-foreground text-xs">
                                    Trace ID: {trace.trace_data.trace_id || 'Available'}
                                  </p>
                                )}
                              </div>
                            ))}
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-center text-muted-foreground py-8 text-sm">
                      Generate an agent to see evaluation traces
                    </p>
                  )}
                </TabsContent>
              </Tabs>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}

// Helper Components
function ConnectionStatus({ 
  service, 
  connected,
  icon
}: { 
  service: string; 
  connected: boolean;
  icon: React.ReactNode;
}) {
  return (
    <div className="flex items-center justify-between p-2 bg-secondary rounded">
      <div className="flex items-center gap-2">
        {icon}
        <span className="text-sm">{service}</span>
      </div>
      <div className={`w-2 h-2 rounded-full ${
        connected ? 'bg-green-500' : 'bg-gray-400'
      }`} />
    </div>
  );
}

function ActionDisplay({ action }: { action: any }) {
  const getActionIcon = (type: string) => {
    switch (type) {
      case 'sms': return <MessageSquare className="w-4 h-4" />;
      case 'calendar': return <Calendar className="w-4 h-4" />;
      case 'agent_generation': return <Brain className="w-4 h-4" />;
      case 'demo_task': return <Activity className="w-4 h-4" />;
      default: return <ChevronRight className="w-4 h-4" />;
    }
  };

  return (
    <div className="flex items-start gap-2">
      <span className="mt-0.5">{getActionIcon(action.type)}</span>
      <div className="flex-1">
        <p className="text-sm font-medium">{action.type}</p>
        {action.status && (
          <p className="text-xs text-muted-foreground">
            Status: {action.status}
          </p>
        )}
        <p className="text-xs text-muted-foreground">
          {new Date(action.timestamp).toLocaleTimeString()}
        </p>
      </div>
    </div>
  );
}