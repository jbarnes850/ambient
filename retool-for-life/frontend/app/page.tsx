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
  Clock,
  Smartphone,
  Search,
  ShoppingCart,
  Shield,
  Zap,
  Target,
  TrendingUp,
  Timer,
  Cpu,
  AlertTriangle,
  Info,
  X
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
  const [rlaifHistory, setRlaifHistory] = useState<any[]>([]);
  const [showAllTools, setShowAllTools] = useState(false);
  const [showMetricsModal, setShowMetricsModal] = useState(false);
  const [showTracesModal, setShowTracesModal] = useState(false);
  const [showUpdatesModal, setShowUpdatesModal] = useState(false);
  
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
              <h2 className="text-lg font-semibold">How It Works</h2>
            </div>
            <p className="text-sm text-muted-foreground">
              The system creates multiple agent versions, tests them, and picks the best one for your needs.
              It tracks how well your agent performs and updates it over time to work better.
            </p>
          </div>
        )}

        {/* Agent Capabilities Section */}
        {!agentStatus && (
          <Card className="mb-6">
            <CardHeader>
              <CardTitle>Available Tools</CardTitle>
              <CardDescription>Functions the agent can use to help with wellness goals</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {/* Key Tools */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <CapabilityCard
                    icon={<Heart className="w-5 h-5" />}
                    title="Health Data"
                    description="Access sleep, activity, stress, and hydration data"
                    examples={["Sleep: 7.2hrs, 85% quality", "Steps: 8,456 today"]}
                  />
                  <CapabilityCard
                    icon={<MessageSquare className="w-5 h-5" />}
                    title="Send Messages"
                    description="Send wellness reminders via SMS or WhatsApp"
                    examples={["Sleep reminder at 10pm", "Hydration check-ins"]}
                  />
                  <CapabilityCard
                    icon={<ShoppingCart className="w-5 h-5" />}
                    title="Make Purchases"
                    description="Buy products with required approval"
                    examples={["Order approved supplements", "Compare prices"]}
                  />
                </div>
                
                {/* Show All Tools Toggle */}
                <div className="text-center">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setShowAllTools(!showAllTools)}
                    className="text-xs"
                  >
                    {showAllTools ? 'Hide additional tools' : 'Show all 8 tools'}
                    <ChevronRight className={`w-3 h-3 ml-1 transition-transform ${showAllTools ? 'rotate-90' : ''}`} />
                  </Button>
                </div>
                
                {/* Additional Tools - Collapsed */}
                {showAllTools && (
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-3">
                    <CompactCapabilityCard
                      icon={<Calendar className="w-4 h-4" />}
                      title="Calendar Changes"
                      description="Schedule adjustments for better wellness"
                    />
                    <CompactCapabilityCard
                      icon={<Smartphone className="w-4 h-4" />}
                      title="Control Devices"
                      description="Run iOS shortcuts to control apps"
                    />
                    <CompactCapabilityCard
                      icon={<Search className="w-4 h-4" />}
                      title="Find Products"
                      description="Search for wellness products"
                    />
                    <CompactCapabilityCard
                      icon={<Shield className="w-4 h-4" />}
                      title="Request Approval"
                      description="Ask permission before actions"
                    />
                    <CompactCapabilityCard
                      icon={<Target className="w-4 h-4" />}
                      title="Learn and Improve"
                      description="Update behavior over time"
                    />
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Current Action */}
        {agentStatus && (
          <Card className="mb-6">
            <CardHeader>
              <CardTitle>Agent Status</CardTitle>
              <CardDescription>Current activity and progress</CardDescription>
            </CardHeader>
            <CardContent>
              <CurrentActionDisplay demoResults={demoResults} isDemoRunning={isDemoRunning} />
            </CardContent>
          </Card>
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
              <CardDescription>Live updates and approval requests</CardDescription>
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
                        <EnhancedActionDisplay action={msg} />
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
              <CardTitle>Performance</CardTitle>
              <CardDescription>Agent effectiveness and improvement tracking</CardDescription>
            </CardHeader>
            <CardContent>
              <PerformanceSummary 
                performance={agentStatus?.performance} 
                recentActions={agentStatus?.recent_actions}
                evaluationTraces={evaluationTraces}
                agentVersion={agentStatus?.agent?.version}
                onShowMetrics={() => setShowMetricsModal(true)}
                onShowTraces={() => setShowTracesModal(true)}
                onShowUpdates={() => setShowUpdatesModal(true)}
              />
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Modal Overlays */}
      <MetricsModal 
        isOpen={showMetricsModal}
        onClose={() => setShowMetricsModal(false)}
        performance={agentStatus?.performance}
      />

      <TracesModal 
        isOpen={showTracesModal}
        onClose={() => setShowTracesModal(false)}
        evaluationTraces={evaluationTraces}
      />

      <UpdatesModal 
        isOpen={showUpdatesModal}
        onClose={() => setShowUpdatesModal(false)}
        agentVersion={agentStatus?.agent?.version}
        performance={agentStatus?.performance}
      />
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

// Enhanced helper components

function CapabilityCard({ 
  icon, 
  title, 
  description, 
  examples 
}: { 
  icon: React.ReactNode; 
  title: string; 
  description: string; 
  examples: string[]; 
}) {
  return (
    <div className="p-4 border rounded-lg space-y-3 hover:bg-secondary/50 transition-colors">
      <div className="flex items-center gap-2">
        <span className="text-primary">{icon}</span>
        <h3 className="font-medium text-sm">{title}</h3>
      </div>
      <p className="text-xs text-muted-foreground">{description}</p>
      <div className="space-y-1">
        {examples.map((example, idx) => (
          <div key={idx} className="text-xs bg-background border rounded px-2 py-1">
            {example}
          </div>
        ))}
      </div>
    </div>
  );
}

function CompactCapabilityCard({ 
  icon, 
  title, 
  description
}: { 
  icon: React.ReactNode; 
  title: string; 
  description: string; 
}) {
  return (
    <div className="p-3 border rounded space-y-2 hover:bg-secondary/50 transition-colors">
      <div className="flex items-center gap-2">
        <span className="text-primary">{icon}</span>
        <h4 className="font-medium text-xs">{title}</h4>
      </div>
      <p className="text-xs text-muted-foreground">{description}</p>
    </div>
  );
}

function PerformanceSummary({ 
  performance, 
  recentActions, 
  evaluationTraces, 
  agentVersion,
  onShowMetrics,
  onShowTraces,
  onShowUpdates
}: { 
  performance?: Record<string, number>; 
  recentActions?: any[]; 
  evaluationTraces?: any; 
  agentVersion?: number;
  onShowMetrics: () => void;
  onShowTraces: () => void;
  onShowUpdates: () => void;
}) {
  if (!performance) {
    return (
      <div className="text-center py-8 space-y-2">
        <Target className="w-8 h-8 text-muted-foreground mx-auto" />
        <p className="text-sm text-muted-foreground">Performance data will appear after agent begins working</p>
      </div>
    );
  }

  const overallScore = Object.values(performance).reduce((acc, val) => acc + val, 0) / Object.values(performance).length;
  const scorePercentage = Math.round(overallScore * 100);

  return (
    <div className="space-y-4">
      {/* Overall Score */}
      <div className="text-center space-y-2">
        <div className="text-3xl font-bold text-primary">{scorePercentage}%</div>
        <div className="flex items-center justify-center gap-1">
          <span className="text-sm text-muted-foreground">Overall Performance</span>
          <MetricStatusIcon value={overallScore} />
        </div>
        <Progress value={scorePercentage} className="h-2" />
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-2 gap-4 text-center">
        <div className="space-y-1">
          <div className="text-lg font-semibold">{agentVersion || 1}</div>
          <div className="text-xs text-muted-foreground">Agent Version</div>
        </div>
        <div className="space-y-1">
          <div className="text-lg font-semibold">{recentActions?.length || 0}</div>
          <div className="text-xs text-muted-foreground">Actions Completed</div>
        </div>
      </div>

      {/* View Details Links */}
      <div className="space-y-2 text-center">
        <Button 
          variant="outline" 
          size="sm" 
          className="w-full"
          onClick={onShowMetrics}
        >
          View Detailed Metrics
        </Button>
        {evaluationTraces && (
          <Button 
            variant="outline" 
            size="sm" 
            className="w-full"
            onClick={onShowTraces}
          >
            View Test Results
          </Button>
        )}
        {agentVersion && agentVersion > 1 && (
          <Button 
            variant="outline" 
            size="sm" 
            className="w-full"
            onClick={onShowUpdates}
          >
            View Update History
          </Button>
        )}
      </div>

      {/* Recent Activity Preview */}
      {recentActions && recentActions.length > 0 && (
        <div className="space-y-2">
          <h4 className="text-sm font-medium">Recent Activity</h4>
          <div className="space-y-1">
            {recentActions.slice(0, 2).map((action, idx) => (
              <div key={idx} className="flex items-center justify-between text-xs p-2 bg-secondary rounded">
                <span className="font-medium">{action.action}</span>
                <Badge variant={action.status === 'completed' ? 'default' : 'secondary'} className="text-xs">
                  {action.status}
                </Badge>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function CurrentActionDisplay({ 
  demoResults, 
  isDemoRunning 
}: { 
  demoResults: any[]; 
  isDemoRunning: boolean; 
}) {
  const workflowSteps = [
    { time: "09:00", title: "Morning Health Check", description: "Check sleep data and send recommendations" },
    { time: "19:30", title: "Evening Reminder", description: "Send bedtime routine reminder" },
    { time: "22:00", title: "Bedtime Setup", description: "Lock apps and enable sleep mode" },
    { time: "22:05", title: "Find Sleep Aids", description: "Search for sleep supplements" },
    { time: "22:06", title: "Complete Purchase", description: "Buy approved products" }
  ];

  const completedSteps = demoResults.length;
  const totalSteps = workflowSteps.length;
  const currentStep = isDemoRunning ? completedSteps : Math.min(completedSteps, totalSteps - 1);
  const progressPercentage = (completedSteps / totalSteps) * 100;

  return (
    <div className="space-y-4">
      {/* Progress Indicator */}
      <div className="space-y-2">
        <div className="flex justify-between text-sm">
          <span>Daily Progress</span>
          <span className="text-muted-foreground">
            {completedSteps} of {totalSteps} completed
          </span>
        </div>
        <Progress value={progressPercentage} className="h-2" />
      </div>

      {/* Current Action */}
      {currentStep < totalSteps && (
        <div className="p-4 border rounded-lg bg-primary/5 border-primary/20">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <div className="text-lg font-semibold text-primary">
                {workflowSteps[currentStep].time}
              </div>
              <Badge variant={isDemoRunning ? "default" : "secondary"}>
                {isDemoRunning ? "Running" : "Next"}
              </Badge>
            </div>
            {isDemoRunning && (
              <div className="flex items-center gap-1 text-sm text-muted-foreground">
                <Clock className="w-3 h-3 animate-spin" />
                <span>Processing</span>
              </div>
            )}
          </div>
          <h3 className="font-medium">{workflowSteps[currentStep].title}</h3>
          <p className="text-sm text-muted-foreground">{workflowSteps[currentStep].description}</p>
        </div>
      )}

      {/* Completed Status */}
      {completedSteps === totalSteps && !isDemoRunning && (
        <div className="p-4 border rounded-lg bg-green-50 border-green-200">
          <div className="flex items-center gap-2 mb-2">
            <CheckCircle className="w-5 h-5 text-green-600" />
            <h3 className="font-medium text-green-800">Daily Sequence Complete</h3>
          </div>
          <p className="text-sm text-green-700">All wellness actions completed successfully</p>
        </div>
      )}

      {/* Recent Completions */}
      {demoResults.length > 0 && (
        <div className="space-y-2">
          <h4 className="text-sm font-medium">Recent Actions</h4>
          <div className="space-y-1">
            {demoResults.slice(-2).map((result, idx) => (
              <div key={idx} className="flex items-center gap-2 text-sm">
                <CheckCircle className="w-3 h-3 text-green-500" />
                <span className="font-medium">{result.time}</span>
                <span className="text-muted-foreground">{result.description}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function WorkflowStep({ 
  time, 
  title, 
  description, 
  tools, 
  status 
}: { 
  time: string; 
  title: string; 
  description: string; 
  tools: string[]; 
  status: string; 
}) {
  return (
    <div className="flex items-start gap-4 p-4 border rounded-lg">
      <div className="flex flex-col items-center">
        <div className="text-sm font-medium text-primary">{time}</div>
        <div className={`w-2 h-2 rounded-full mt-2 ${
          status === 'completed' ? 'bg-green-500' : 'bg-gray-300'
        }`} />
      </div>
      <div className="flex-1 space-y-2">
        <div className="flex items-center justify-between">
          <h4 className="font-medium">{title}</h4>
          <Badge variant={status === 'completed' ? 'default' : 'secondary'}>
            {status}
          </Badge>
        </div>
        <p className="text-sm text-muted-foreground">{description}</p>
        <div className="flex gap-1 flex-wrap">
          {tools.map((tool, idx) => (
            <Badge key={idx} variant="outline" className="text-xs">
              {tool}
            </Badge>
          ))}
        </div>
      </div>
    </div>
  );
}

function MetricTooltip({ metric }: { metric: string }) {
  const tooltips: Record<string, string> = {
    task_completion: "How often the agent completes wellness tasks successfully",
    user_engagement: "How well users respond to agent messages and suggestions",
    timing_accuracy: "Whether actions happen at the right times for the user",
    resource_efficiency: "How efficiently the agent uses system resources",
    safety_compliance: "Whether the agent properly asks for approval when needed"
  };

  return (
    <div className="group relative">
      <Info className="w-3 h-3 text-muted-foreground cursor-help" />
      <div className="absolute left-4 bottom-0 hidden group-hover:block z-10 w-64 p-2 bg-popover border rounded-md shadow-md text-xs">
        {tooltips[metric] || "Measures how well the agent is working"}
      </div>
    </div>
  );
}

function MetricStatusIcon({ value }: { value: number }) {
  if (value >= 0.9) return <CheckCircle className="w-3 h-3 text-green-500" />;
  if (value >= 0.7) return <Clock className="w-3 h-3 text-yellow-500" />;
  return <AlertTriangle className="w-3 h-3 text-red-500" />;
}

function getMetricColor(value: number): string {
  if (value >= 0.9) return "bg-green-500";
  if (value >= 0.7) return "bg-yellow-500";
  return "bg-red-500";
}

function EnhancedActionDisplay({ action }: { action: any }) {
  const getActionIcon = (type: string) => {
    switch (type) {
      case 'sms': return <MessageSquare className="w-4 h-4" />;
      case 'calendar': return <Calendar className="w-4 h-4" />;
      case 'agent_generation': return <Brain className="w-4 h-4" />;
      case 'demo_task': return <Activity className="w-4 h-4" />;
      case 'health_check': return <Heart className="w-4 h-4" />;
      case 'product_search': return <Search className="w-4 h-4" />;
      case 'commerce': return <ShoppingCart className="w-4 h-4" />;
      case 'ios_shortcut': return <Smartphone className="w-4 h-4" />;
      default: return <ChevronRight className="w-4 h-4" />;
    }
  };

  return (
    <div className="space-y-2">
      <div className="flex items-start gap-2">
        <span className="mt-0.5">{getActionIcon(action.type)}</span>
        <div className="flex-1">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium">{action.type}</p>
            <Badge variant={action.status === 'completed' ? 'default' : 'secondary'} className="text-xs">
              {action.status || 'processing'}
            </Badge>
          </div>
          <p className="text-xs text-muted-foreground">
            {new Date(action.timestamp).toLocaleTimeString()}
          </p>
        </div>
      </div>
      
      {/* Show agent reasoning if available */}
      {action.reasoning && (
        <div className="ml-6 p-2 bg-background border rounded text-xs">
          <span className="font-medium">Agent Reasoning: </span>
          <span className="text-muted-foreground">{action.reasoning}</span>
        </div>
      )}
      
      {/* Show tool calls if available */}
      {action.tool_calls && action.tool_calls.length > 0 && (
        <div className="ml-6 space-y-1">
          {action.tool_calls.map((tool: any, idx: number) => (
            <div key={idx} className="flex items-center gap-2 text-xs">
              <Zap className="w-3 h-3 text-blue-500" />
              <span className="font-medium">{tool.function?.name || tool.name}</span>
              <span className="text-muted-foreground">
                {tool.status || 'executed'}
              </span>
            </div>
          ))}
        </div>
      )}
      
      {/* Show output if available */}
      {action.output && (
        <div className="ml-6 p-2 bg-background border rounded text-xs">
          <span className="font-medium">Result: </span>
          <span className="text-muted-foreground">
            {typeof action.output === 'string' ? action.output : JSON.stringify(action.output).slice(0, 100)}
          </span>
        </div>
      )}
    </div>
  );
}

function RLAIFImprovementDisplay({ 
  currentVersion, 
  performance 
}: { 
  currentVersion: number; 
  performance: Record<string, number>; 
}) {
  // Simulate historical performance data (in a real app, this would come from the backend)
  const generateHistoricalData = () => {
    const data = [];
    for (let version = 1; version <= currentVersion; version++) {
      const basePerformance = {
        task_completion: 0.7 + (version - 1) * 0.05,
        user_engagement: 0.8 + (version - 1) * 0.03,
        timing_accuracy: 0.75 + (version - 1) * 0.04,
        resource_efficiency: 0.7 + (version - 1) * 0.06,
        safety_compliance: 0.95 + (version - 1) * 0.01
      };
      
      // Current version uses actual performance data
      if (version === currentVersion) {
        data.push({
          version,
          performance,
          improvements: version > 1 ? ['Better timing for tasks', 'Improved user interactions'] : []
        });
      } else {
        data.push({
          version,
          performance: basePerformance,
          improvements: version > 1 ? ['Better responses', 'Smarter tool choices'] : []
        });
      }
    }
    return data;
  };

  const historyData = generateHistoricalData();

  return (
    <div className="space-y-3">
      {historyData.map((data, idx) => (
        <div key={data.version} className={`p-3 border rounded space-y-2 ${
          data.version === currentVersion ? 'border-primary bg-primary/5' : ''
        }`}>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Badge variant={data.version === currentVersion ? 'default' : 'secondary'}>
                v{data.version}
              </Badge>
              {data.version === currentVersion && (
                <span className="text-xs text-primary font-medium">Current</span>
              )}
            </div>
            <div className="text-xs text-muted-foreground">
              Avg: {(Object.values(data.performance).reduce((a, b) => a + b, 0) / Object.values(data.performance).length * 100).toFixed(0)}%
            </div>
          </div>
          
          {idx > 0 && data.improvements.length > 0 && (
            <div className="space-y-1">
              <h6 className="text-xs font-medium text-green-600">What Changed:</h6>
              {data.improvements.map((improvement, impIdx) => (
                <div key={impIdx} className="flex items-center gap-1 text-xs text-muted-foreground">
                  <TrendingUp className="w-3 h-3 text-green-500" />
                  <span>{improvement}</span>
                </div>
              ))}
            </div>
          )}
          
          <div className="grid grid-cols-2 gap-2 text-xs">
            {Object.entries(data.performance).map(([metric, value]) => (
              <div key={metric} className="flex justify-between">
                <span className="capitalize">{metric.replace(/_/g, ' ').slice(0, 8)}...</span>
                <span className="font-medium">{(value * 100).toFixed(0)}%</span>
              </div>
            ))}
          </div>
        </div>
      ))}
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

// Modal Components
function MetricsModal({ 
  isOpen, 
  onClose, 
  performance 
}: { 
  isOpen: boolean; 
  onClose: () => void; 
  performance?: Record<string, number>; 
}) {
  if (!isOpen) return null;

  const tooltips: Record<string, string> = {
    task_completion: "How often the agent completes wellness tasks successfully",
    user_engagement: "How well users respond to agent messages and suggestions",
    timing_accuracy: "Whether actions happen at the right times for the user",
    resource_efficiency: "How efficiently the agent uses system resources",
    safety_compliance: "Whether the agent properly asks for approval when needed"
  };

  const getMetricColor = (value: number): string => {
    if (value >= 0.9) return "bg-green-500";
    if (value >= 0.7) return "bg-yellow-500";
    return "bg-red-500";
  };

  const MetricStatusIcon = ({ value }: { value: number }) => {
    if (value >= 0.9) return <CheckCircle className="w-3 h-3 text-green-500" />;
    if (value >= 0.7) return <Clock className="w-3 h-3 text-yellow-500" />;
    return <AlertTriangle className="w-3 h-3 text-red-500" />;
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-background rounded-lg shadow-lg max-w-2xl w-full max-h-[80vh] overflow-y-auto">
        <div className="flex items-center justify-between p-4 border-b">
          <h2 className="text-lg font-semibold">Detailed Reward Function Metrics</h2>
          <Button variant="ghost" size="sm" onClick={onClose}>
            <X className="w-4 h-4" />
          </Button>
        </div>
        
        <div className="p-4 space-y-4">
          <p className="text-sm text-muted-foreground">
            The RLAIF system tracks these five reward dimensions to optimize agent performance:
          </p>
          
          {performance && Object.entries(performance).map(([key, value]) => (
            <div key={key} className="space-y-2 p-4 border rounded-lg">
              <div className="flex justify-between items-center">
                <div className="flex items-center gap-2">
                  <h3 className="font-medium capitalize">{key.replace(/_/g, ' ')}</h3>
                  <MetricStatusIcon value={value} />
                </div>
                <span className="text-lg font-semibold">{(value * 100).toFixed(0)}%</span>
              </div>
              
              <Progress value={value * 100} className={`h-2 ${getMetricColor(value)}`} />
              
              <p className="text-xs text-muted-foreground">
                {tooltips[key] || "Measures how well the agent is working"}
              </p>
              
              <div className="text-xs space-y-1">
                <div className="font-medium">Technical Details:</div>
                <div className="text-muted-foreground">
                  Raw Score: {value.toFixed(3)} | 
                  Weight: 1.0 | 
                  Threshold: {value >= 0.7 ? "✓ Met" : "✗ Below"} (0.7)
                </div>
              </div>
            </div>
          ))}
          
          <div className="p-4 bg-secondary rounded-lg">
            <h3 className="font-medium mb-2">Reward Function Formula</h3>
            <code className="text-xs bg-background p-2 rounded block">
              reward = (task_completion + user_engagement + timing_accuracy + resource_efficiency + safety_compliance) / 5
            </code>
            <p className="text-xs text-muted-foreground mt-2">
              Overall performance below 0.8 triggers automatic agent improvement via RLAIF.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

function TracesModal({ 
  isOpen, 
  onClose, 
  evaluationTraces 
}: { 
  isOpen: boolean; 
  onClose: () => void; 
  evaluationTraces?: any; 
}) {
  const [selectedTrace, setSelectedTrace] = useState<any>(null);
  const [viewMode, setViewMode] = useState<'summary' | 'detailed'>('summary');
  const [expandedSpans, setExpandedSpans] = useState<Set<string>>(new Set());

  if (!isOpen) return null;

  const fetchFullTraceData = async (traceId: string) => {
    try {
      const response = await fetch(`/api/traces/${traceId}/spans`);
      if (response.ok) {
        const data = await response.json();
        setSelectedTrace(data);
        setViewMode('detailed');
      }
    } catch (error) {
      console.error('Failed to fetch trace data:', error);
    }
  };

  const toggleSpanExpansion = (spanId: string) => {
    const newExpanded = new Set(expandedSpans);
    if (newExpanded.has(spanId)) {
      newExpanded.delete(spanId);
    } else {
      newExpanded.add(spanId);
    }
    setExpandedSpans(newExpanded);
  };

  const renderSpanHierarchy = (spans: any[], level: number = 0) => {
    return spans.map((span: any) => (
      <div key={span.span_id} className={`ml-${level * 4} space-y-2`}>
        <div 
          className="p-2 bg-secondary rounded border-l-2 border-primary/20 cursor-pointer hover:bg-secondary/80"
          onClick={() => toggleSpanExpansion(span.span_id)}
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="text-xs font-mono bg-primary/10 px-1 rounded">
                {span.span_type}
              </span>
              <span className="text-sm">{span.span_id}</span>
              {span.children && span.children.length > 0 && (
                <Badge variant="outline" className="text-xs">
                  {span.children.length} children
                </Badge>
              )}
            </div>
            <div className="flex items-center gap-2 text-xs text-muted-foreground">
              {span.duration_ms && <span>{span.duration_ms.toFixed(2)}ms</span>}
              <span>{expandedSpans.has(span.span_id) ? '▼' : '▶'}</span>
            </div>
          </div>
          
          {expandedSpans.has(span.span_id) && span.span_data && (
            <div className="mt-2 p-2 bg-background rounded text-xs">
              <div className="font-medium mb-1">Span Data:</div>
              <pre className="whitespace-pre-wrap text-muted-foreground">
                {JSON.stringify(span.span_data, null, 2)}
              </pre>
            </div>
          )}
        </div>
        
        {span.children && span.children.length > 0 && (
          <div className="ml-4">
            {renderSpanHierarchy(span.children, level + 1)}
          </div>
        )}
      </div>
    ));
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-background rounded-lg shadow-lg max-w-6xl w-full max-h-[90vh] overflow-hidden flex flex-col">
        <div className="flex items-center justify-between p-4 border-b">
          <div className="flex items-center gap-4">
            <h2 className="text-lg font-semibold">Agent Evaluation Traces</h2>
            {selectedTrace && (
              <Button 
                variant="outline" 
                size="sm" 
                onClick={() => { setSelectedTrace(null); setViewMode('summary'); }}
              >
                ← Back to Summary
              </Button>
            )}
          </div>
          <Button variant="ghost" size="sm" onClick={onClose}>
            <X className="w-4 h-4" />
          </Button>
        </div>
        
        <div className="flex-1 overflow-y-auto">
          {viewMode === 'detailed' && selectedTrace ? (
            <div className="p-4 space-y-4">
              <div className="p-4 bg-secondary rounded-lg">
                <h3 className="font-medium mb-2">Trace Details: {selectedTrace.trace_id}</h3>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>Total Spans: {selectedTrace.total_spans}</div>
                  <div>Events: {selectedTrace.events?.length || 0}</div>
                </div>
              </div>

              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <h3 className="font-medium">Execution Hierarchy</h3>
                  <div className="flex gap-2">
                    <Button 
                      variant="outline" 
                      size="sm"
                      onClick={() => setExpandedSpans(new Set(selectedTrace.spans.map((s: any) => s.span_id)))}
                    >
                      Expand All
                    </Button>
                    <Button 
                      variant="outline" 
                      size="sm"
                      onClick={() => setExpandedSpans(new Set())}
                    >
                      Collapse All
                    </Button>
                  </div>
                </div>
                
                <div className="space-y-1">
                  {selectedTrace.execution_hierarchy && selectedTrace.execution_hierarchy.length > 0 ? (
                    renderSpanHierarchy(selectedTrace.execution_hierarchy)
                  ) : (
                    <div className="p-4 bg-secondary rounded">
                      <div className="text-sm font-medium mb-2">Flat Span List:</div>
                      {selectedTrace.spans.map((span: any, idx: number) => (
                        <div key={idx} className="p-2 bg-background rounded mb-2">
                          <div className="flex items-center justify-between">
                            <span className="text-xs font-mono bg-primary/10 px-1 rounded">
                              {span.span_type}
                            </span>
                            <span className="text-xs text-muted-foreground">
                              {span.duration_ms?.toFixed(2)}ms
                            </span>
                          </div>
                          {span.span_data && Object.keys(span.span_data).length > 0 && (
                            <pre className="text-xs text-muted-foreground mt-1 whitespace-pre-wrap">
                              {JSON.stringify(span.span_data, null, 2)}
                            </pre>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                {selectedTrace.events && selectedTrace.events.length > 0 && (
                  <div className="space-y-2">
                    <h3 className="font-medium">Events</h3>
                    <div className="space-y-1">
                      {selectedTrace.events.map((event: any, idx: number) => (
                        <div key={idx} className="p-2 bg-secondary rounded text-xs">
                          <div className="font-medium">{event.event_type}</div>
                          <div className="text-muted-foreground">{event.timestamp}</div>
                          {event.data && (
                            <pre className="mt-1 whitespace-pre-wrap">
                              {JSON.stringify(event.data, null, 2)}
                            </pre>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div className="p-4 space-y-4">
              {evaluationTraces ? (
                <div className="space-y-4">
                  <p className="text-sm text-muted-foreground">
                    Complete evaluation results showing agent performance across test scenarios with full OpenAI SDK tracing data.
                  </p>
                  
                  {/* Overall comparison */}
                  <div className="p-4 bg-secondary rounded-lg space-y-3">
                    <h3 className="font-medium">Performance Comparison</h3>
                    <div className="space-y-2">
                      {Object.entries(evaluationTraces)
                        .map(([name, traces]: [string, any]) => ({
                          name,
                          avgScore: traces.reduce((acc: number, t: any) => acc + (t.score || 0), 0) / traces.length
                        }))
                        .sort((a, b) => b.avgScore - a.avgScore)
                        .map((agent, idx) => (
                          <div key={agent.name} className="flex items-center justify-between p-2 bg-background rounded">
                            <div className="flex items-center gap-2">
                              {idx === 0 && <TrendingUp className="w-4 h-4 text-green-500" />}
                              <span className={`text-sm ${idx === 0 ? 'font-medium' : ''}`}>
                                {agent.name} {idx === 0 && '(Selected)'}
                              </span>
                            </div>
                            <div className="flex items-center gap-2">
                              <Progress value={agent.avgScore * 100} className="w-20 h-2" />
                              <span className="text-sm font-medium w-12">
                                {(agent.avgScore * 100).toFixed(0)}%
                              </span>
                            </div>
                          </div>
                        ))
                      }
                    </div>
                  </div>
                  
                  {/* Detailed traces for each agent */}
                  {Object.entries(evaluationTraces).map(([agentName, traces]: [string, any]) => (
                    <div key={agentName} className="space-y-3 border rounded-lg p-4">
                      <div className="flex items-center justify-between">
                        <h3 className="font-medium">{agentName}</h3>
                        <Badge variant="outline">
                          Avg: {(traces.reduce((acc: number, t: any) => acc + (t.score || 0), 0) / traces.length * 100).toFixed(0)}%
                        </Badge>
                      </div>
                      
                      <div className="space-y-3">
                        {traces.map((trace: any, idx: number) => (
                          <div key={idx} className="p-3 bg-secondary rounded space-y-2">
                            <div className="flex justify-between items-center">
                              <span className="font-medium text-sm">{trace.scenario}</span>
                              <div className="flex items-center gap-2">
                                <Badge variant={trace.score >= 0.8 ? 'default' : 'secondary'}>
                                  {(trace.score * 100).toFixed(0)}%
                                </Badge>
                                {trace.trace_data?.trace_id && (
                                  <Button 
                                    variant="outline" 
                                    size="sm"
                                    onClick={() => fetchFullTraceData(trace.trace_data.trace_id)}
                                  >
                                    View Details
                                  </Button>
                                )}
                              </div>
                            </div>
                            
                            {trace.reasoning && (
                              <div className="space-y-1">
                                <div className="text-xs font-medium">Agent Reasoning:</div>
                                <div className="text-xs text-muted-foreground bg-background p-2 rounded">
                                  {trace.reasoning}
                                </div>
                              </div>
                            )}
                            
                            {trace.tools_used && (
                              <div className="space-y-1">
                                <div className="text-xs font-medium">Tools Used:</div>
                                <div className="flex gap-1 flex-wrap">
                                  {trace.tools_used.map((tool: string, toolIdx: number) => (
                                    <Badge key={toolIdx} variant="outline" className="text-xs">
                                      {tool}
                                    </Badge>
                                  ))}
                                </div>
                              </div>
                            )}
                            
                            {trace.trace_data && (
                              <div className="space-y-1">
                                <div className="text-xs font-medium">OpenAI SDK Trace:</div>
                                <div className="text-xs text-muted-foreground space-y-1">
                                  <div>Trace ID: <code className="bg-background px-1 rounded">{trace.trace_data.trace_id}</code></div>
                                  {trace.trace_data.total_duration_ms && <div>Duration: {trace.trace_data.total_duration_ms.toFixed(2)}ms</div>}
                                  {trace.trace_data.spans && <div>Spans: {trace.trace_data.spans.length}</div>}
                                  {trace.trace_data.llm_generations && <div>LLM Calls: {trace.trace_data.llm_generations.length}</div>}
                                  {trace.trace_data.function_calls && <div>Function Calls: {trace.trace_data.function_calls.length}</div>}
                                </div>
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
                  
                  <div className="p-4 bg-secondary rounded-lg">
                    <h3 className="font-medium mb-2">Enhanced Tracing Capabilities</h3>
                    <div className="text-xs text-muted-foreground space-y-1">
                      <div>• Complete OpenAI Agents SDK trace capture with spans and events</div>
                      <div>• Agent reasoning, LLM generations, and function call tracking</div>
                      <div>• Hierarchical execution flow visualization</div>
                      <div>• Performance metrics: 50% tool usage + 50% outcome quality</div>
                      <div>• Click "View Details" to explore full trace execution logs</div>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="text-center py-8">
                  <Brain className="w-12 h-12 text-muted-foreground mx-auto mb-2" />
                  <p className="text-muted-foreground">No evaluation traces available</p>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function UpdatesModal({ 
  isOpen, 
  onClose, 
  agentVersion, 
  performance 
}: { 
  isOpen: boolean; 
  onClose: () => void; 
  agentVersion?: number; 
  performance?: Record<string, number>; 
}) {
  if (!isOpen) return null;

  // Generate historical performance data (in a real app, this would come from the backend)
  const generateHistoricalData = () => {
    const data = [];
    const currentVersion = agentVersion || 1;
    for (let version = 1; version <= currentVersion; version++) {
      const basePerformance = {
        task_completion: 0.7 + (version - 1) * 0.05,
        user_engagement: 0.8 + (version - 1) * 0.03,
        timing_accuracy: 0.75 + (version - 1) * 0.04,
        resource_efficiency: 0.7 + (version - 1) * 0.06,
        safety_compliance: 0.95 + (version - 1) * 0.01
      };
      
      // Current version uses actual performance data
      if (version === currentVersion && performance) {
        data.push({
          version,
          performance,
          improvements: version > 1 ? ['Better timing for tasks', 'Improved user interactions'] : [],
          timestamp: new Date(Date.now() - (currentVersion - version) * 24 * 60 * 60 * 1000).toISOString()
        });
      } else {
        data.push({
          version,
          performance: basePerformance,
          improvements: version > 1 ? ['Better responses', 'Smarter tool choices'] : [],
          timestamp: new Date(Date.now() - (currentVersion - version) * 24 * 60 * 60 * 1000).toISOString()
        });
      }
    }
    return data;
  };

  const historyData = generateHistoricalData();

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-background rounded-lg shadow-lg max-w-3xl w-full max-h-[80vh] overflow-y-auto">
        <div className="flex items-center justify-between p-4 border-b">
          <h2 className="text-lg font-semibold">RLAIF Update History</h2>
          <Button variant="ghost" size="sm" onClick={onClose}>
            <X className="w-4 h-4" />
          </Button>
        </div>
        
        <div className="p-4 space-y-4">
          <p className="text-sm text-muted-foreground">
            Complete history of agent updates driven by Reinforcement Learning from AI Feedback (RLAIF).
          </p>
          
          <div className="space-y-4">
            {historyData.map((data, idx) => (
              <div key={data.version} className={`p-4 border rounded-lg space-y-3 ${
                data.version === agentVersion ? 'border-primary bg-primary/5' : ''
              }`}>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <Badge variant={data.version === agentVersion ? 'default' : 'secondary'}>
                      Version {data.version}
                    </Badge>
                    {data.version === agentVersion && (
                      <span className="text-xs text-primary font-medium">Current</span>
                    )}
                    <span className="text-xs text-muted-foreground">
                      {new Date(data.timestamp).toLocaleDateString()}
                    </span>
                  </div>
                  <div className="text-sm font-medium">
                    {(Object.values(data.performance).reduce((a, b) => a + b, 0) / Object.values(data.performance).length * 100).toFixed(0)}% avg
                  </div>
                </div>
                
                {idx > 0 && data.improvements.length > 0 && (
                  <div className="space-y-2">
                    <h4 className="text-sm font-medium text-green-600">Changes Applied:</h4>
                    <div className="space-y-1">
                      {data.improvements.map((improvement, impIdx) => (
                        <div key={impIdx} className="flex items-center gap-2 text-sm">
                          <TrendingUp className="w-3 h-3 text-green-500" />
                          <span>{improvement}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
                
                <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                  {Object.entries(data.performance).map(([metric, value]) => (
                    <div key={metric} className="space-y-1">
                      <div className="flex justify-between text-xs">
                        <span className="capitalize">{metric.replace(/_/g, ' ').slice(0, 12)}...</span>
                        <span className="font-medium">{(value * 100).toFixed(0)}%</span>
                      </div>
                      <Progress value={value * 100} className="h-1" />
                    </div>
                  ))}
                </div>
                
                {idx > 0 && (
                  <div className="text-xs text-muted-foreground space-y-1">
                    <div className="font-medium">Update Trigger:</div>
                    <div>Average performance below 0.8 threshold detected</div>
                    <div>AI analysis identified improvement opportunities</div>
                    <div>New instructions generated and applied automatically</div>
                  </div>
                )}
              </div>
            ))}
          </div>
          
          <div className="p-4 bg-secondary rounded-lg space-y-3">
            <h3 className="font-medium">RLAIF Process Details</h3>
            <div className="text-sm text-muted-foreground space-y-2">
              <div className="flex items-center gap-2">
                <Target className="w-4 h-4 text-blue-500" />
                <span><strong>Performance Monitoring:</strong> Continuous tracking across 5 reward dimensions</span>
              </div>
              <div className="flex items-center gap-2">
                <Brain className="w-4 h-4 text-purple-500" />
                <span><strong>AI Analysis:</strong> GPT-4.1-mini identifies weak areas and generates improvements</span>
              </div>
              <div className="flex items-center gap-2">
                <TrendingUp className="w-4 h-4 text-green-500" />
                <span><strong>Automatic Updates:</strong> Enhanced instructions deployed without interruption</span>
              </div>
              <div className="flex items-center gap-2">
                <Cpu className="w-4 h-4 text-orange-500" />
                <span><strong>Continuity:</strong> Conversation history and user context preserved</span>
              </div>
            </div>
            
            <div className="mt-3 p-3 bg-background rounded border">
              <div className="text-xs font-medium mb-1">Next Update Criteria:</div>
              <div className="text-xs text-muted-foreground">
                Average performance &lt; 0.8 OR individual metric &lt; 0.7 for 3+ days
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}