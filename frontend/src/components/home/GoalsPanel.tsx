'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { CheckCircle2, Circle, Plus, X, Target, Loader2, Pin } from 'lucide-react';
import toast from 'react-hot-toast';
import { goalsService } from '@/services/goals';
import type { UserGoal, CreateGoalRequest } from '@/types';

// ── Category config ────────────────────────────────────────────────────────────

const CATEGORY_OPTIONS = [
  { value: 'general', label: 'General' },
  { value: 'weight', label: 'Weight' },
  { value: 'exercise', label: 'Exercise' },
  { value: 'diet', label: 'Diet' },
  { value: 'medication', label: 'Medication' },
  { value: 'sleep', label: 'Sleep' },
  { value: 'lab_result', label: 'Lab Result' },
  { value: 'mental_health', label: 'Mental Health' },
] as const;

const CATEGORY_COLORS: Record<string, string> = {
  weight: 'bg-blue-500/15 text-blue-300',
  exercise: 'bg-green-500/15 text-green-300',
  diet: 'bg-orange-500/15 text-orange-300',
  medication: 'bg-purple-500/15 text-purple-300',
  sleep: 'bg-indigo-500/15 text-indigo-300',
  lab_result: 'bg-cyan-500/15 text-cyan-300',
  mental_health: 'bg-pink-500/15 text-pink-300',
  general: 'bg-white/10 text-[#8B97A8]',
};

// ── Add Goal Modal ─────────────────────────────────────────────────────────────

interface AddGoalModalProps {
  onClose: () => void;
}

function AddGoalModal({ onClose }: AddGoalModalProps) {
  const queryClient = useQueryClient();
  const [goalText, setGoalText] = useState('');
  const [category, setCategory] = useState<CreateGoalRequest['category']>('general');
  const [dueDate, setDueDate] = useState('');
  const [notes, setNotes] = useState('');
  const [isDoctorInstruction, setIsDoctorInstruction] = useState(false);

  const createMutation = useMutation({
    mutationFn: (payload: CreateGoalRequest) => goalsService.createGoal(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['goals'] });
      toast.success('Goal added');
      onClose();
    },
    onError: () => toast.error('Failed to add goal'),
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!goalText.trim()) return;
    createMutation.mutate({
      goal_text: goalText.trim(),
      category,
      due_date: dueDate || undefined,
      notes: notes.trim() || undefined,
      source: isDoctorInstruction ? 'doctor' : 'user',
      is_pinned: isDoctorInstruction,
    });
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      onClick={onClose}
    >
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" />
      <div
        className="relative w-full max-w-md rounded-2xl p-6 shadow-2xl"
        style={{
          backgroundColor: '#0D1117',
          border: '1px solid rgba(255,255,255,0.10)',
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between mb-5">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-[#00D4AA]/15 flex items-center justify-center">
              <Target className="w-4 h-4 text-[#00D4AA]" />
            </div>
            <h2 className="text-base font-semibold text-[#E8EDF5]">New Health Goal</h2>
          </div>
          <button
            onClick={onClose}
            className="text-[#526380] hover:text-[#8B97A8] transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Goal text */}
          <div>
            <label className="block text-xs font-medium text-[#8B97A8] mb-1.5">
              What&apos;s your goal?
            </label>
            <textarea
              value={goalText}
              onChange={(e) => setGoalText(e.target.value)}
              placeholder="e.g. Reduce LDL to under 100 by June, Walk 8,000 steps daily..."
              rows={2}
              className="w-full rounded-lg px-3 py-2.5 text-sm text-[#E8EDF5] placeholder-[#3D4F66] outline-none resize-none transition-colors"
              style={{
                backgroundColor: 'rgba(255,255,255,0.05)',
                border: '1px solid rgba(255,255,255,0.08)',
              }}
              onFocus={(e) =>
                (e.currentTarget.style.border = '1px solid rgba(0,212,170,0.4)')
              }
              onBlur={(e) =>
                (e.currentTarget.style.border = '1px solid rgba(255,255,255,0.08)')
              }
              autoFocus
            />
          </div>

          {/* Category */}
          <div>
            <label className="block text-xs font-medium text-[#8B97A8] mb-1.5">
              Category
            </label>
            <select
              value={category}
              onChange={(e) => setCategory(e.target.value as CreateGoalRequest['category'])}
              className="w-full rounded-lg px-3 py-2.5 text-sm text-[#E8EDF5] outline-none appearance-none cursor-pointer"
              style={{
                backgroundColor: 'rgba(255,255,255,0.05)',
                border: '1px solid rgba(255,255,255,0.08)',
              }}
            >
              {CATEGORY_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value} style={{ backgroundColor: '#0D1117' }}>
                  {opt.label}
                </option>
              ))}
            </select>
          </div>

          {/* Due date (optional) */}
          <div>
            <label className="block text-xs font-medium text-[#8B97A8] mb-1.5">
              Target date <span className="text-[#3D4F66]">(optional)</span>
            </label>
            <input
              type="date"
              value={dueDate}
              onChange={(e) => setDueDate(e.target.value)}
              className="w-full rounded-lg px-3 py-2.5 text-sm text-[#E8EDF5] outline-none"
              style={{
                backgroundColor: 'rgba(255,255,255,0.05)',
                border: '1px solid rgba(255,255,255,0.08)',
                colorScheme: 'dark',
              }}
            />
          </div>

          {/* Doctor instruction toggle */}
          <button
            type="button"
            onClick={() => setIsDoctorInstruction((v) => !v)}
            className="w-full flex items-center gap-2.5 px-3 py-2.5 rounded-lg text-sm transition-colors text-left"
            style={{
              backgroundColor: isDoctorInstruction ? 'rgba(0,212,170,0.08)' : 'rgba(255,255,255,0.03)',
              border: `1px solid ${isDoctorInstruction ? 'rgba(0,212,170,0.25)' : 'rgba(255,255,255,0.07)'}`,
            }}
          >
            <Pin
              className="w-3.5 h-3.5 flex-shrink-0 transition-colors"
              style={{ color: isDoctorInstruction ? '#00D4AA' : '#526380' }}
            />
            <div className="flex-1 min-w-0">
              <span className="font-medium" style={{ color: isDoctorInstruction ? '#00D4AA' : '#8B97A8' }}>
                Doctor&apos;s instruction
              </span>
              <span className="ml-1.5 text-xs" style={{ color: '#526380' }}>
                — pins this goal at the top
              </span>
            </div>
            <div
              className="w-4 h-4 rounded border flex items-center justify-center flex-shrink-0 transition-all"
              style={{
                backgroundColor: isDoctorInstruction ? '#00D4AA' : 'transparent',
                borderColor: isDoctorInstruction ? '#00D4AA' : 'rgba(255,255,255,0.2)',
              }}
            >
              {isDoctorInstruction && (
                <svg className="w-2.5 h-2.5" fill="none" viewBox="0 0 10 10">
                  <path d="M1.5 5l2.5 2.5 4.5-4.5" stroke="#080B10" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
              )}
            </div>
          </button>

          {/* Actions */}
          <div className="flex gap-3 pt-1">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 py-2.5 rounded-lg text-sm font-medium text-[#526380] hover:text-[#8B97A8] transition-colors"
              style={{ backgroundColor: 'rgba(255,255,255,0.04)' }}
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={!goalText.trim() || createMutation.isPending}
              className="flex-1 py-2.5 rounded-lg text-sm font-semibold text-[#080B10] bg-[#00D4AA] hover:bg-[#00BF99] disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2"
            >
              {createMutation.isPending ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : null}
              Add Goal
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// ── Goal row ──────────────────────────────────────────────────────────────────

function GoalRow({ goal }: { goal: UserGoal }) {
  const queryClient = useQueryClient();

  const achieveMutation = useMutation({
    mutationFn: () => goalsService.updateGoal(goal.id, { status: 'achieved' }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['goals'] });
      toast.success('Goal achieved! 🎉');
    },
    onError: () => toast.error('Could not update goal'),
  });

  const deleteMutation = useMutation({
    mutationFn: () => goalsService.deleteGoal(goal.id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['goals'] }),
    onError: () => toast.error('Could not delete goal'),
  });

  const colorClass = CATEGORY_COLORS[goal.category] ?? CATEGORY_COLORS.general;
  const isPinned = goal.is_pinned;
  const isDoctor = goal.source === 'doctor';

  return (
    <div
      className="flex items-start gap-3 group rounded-lg px-2.5 py-2 -mx-2.5 transition-colors"
      style={isPinned ? {
        backgroundColor: 'rgba(0,212,170,0.04)',
        border: '1px solid rgba(0,212,170,0.12)',
        borderRadius: '8px',
      } : undefined}
    >
      <button
        onClick={() => achieveMutation.mutate()}
        disabled={achieveMutation.isPending}
        className="mt-0.5 flex-shrink-0 text-[#3D4F66] hover:text-[#00D4AA] transition-colors"
        aria-label="Mark as achieved"
      >
        {achieveMutation.isPending ? (
          <Loader2 className="w-4 h-4 animate-spin text-[#00D4AA]" />
        ) : (
          <Circle className="w-4 h-4" />
        )}
      </button>

      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-1.5 mb-0.5">
          {isPinned && <Pin className="w-3 h-3 flex-shrink-0" style={{ color: '#00D4AA' }} />}
          <p className="text-sm leading-snug" style={{ color: isPinned ? '#E8EDF5' : '#C8D5E8' }}>{goal.goal_text}</p>
        </div>
        <div className="flex items-center gap-2 flex-wrap">
          {isDoctor && (
            <span className="text-[10px] font-semibold px-1.5 py-0.5 rounded-md"
              style={{ backgroundColor: 'rgba(0,212,170,0.12)', color: '#00D4AA' }}>
              Dr. instruction
            </span>
          )}
          <span className={`text-[10px] font-medium px-1.5 py-0.5 rounded-md ${colorClass}`}>
            {goal.category.replace('_', ' ')}
          </span>
          {goal.due_date && (
            <span className="text-[10px] text-[#3D4F66]">
              by {new Date(goal.due_date + 'T12:00:00').toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
            </span>
          )}
        </div>
      </div>

      <button
        onClick={() => deleteMutation.mutate()}
        disabled={deleteMutation.isPending}
        className="mt-0.5 flex-shrink-0 opacity-0 group-hover:opacity-100 text-[#3D4F66] hover:text-[#F87171] transition-all"
        aria-label="Remove goal"
      >
        <X className="w-3.5 h-3.5" />
      </button>
    </div>
  );
}

// ── Goals Panel ───────────────────────────────────────────────────────────────

export function GoalsPanel() {
  const [showModal, setShowModal] = useState(false);

  const { data: goals = [], isLoading } = useQuery({
    queryKey: ['goals'],
    queryFn: () => goalsService.listGoals('active'),
    staleTime: 60_000,
  });

  if (isLoading) return null;

  // When no goals: show a subtle "Set a goal" prompt instead of hiding entirely
  if (goals.length === 0) {
    return (
      <>
        {showModal && <AddGoalModal onClose={() => setShowModal(false)} />}
        <div
          className="rounded-xl px-5 py-4 flex items-center justify-between"
          style={{
            backgroundColor: 'rgba(255,255,255,0.02)',
            border: '1px dashed rgba(255,255,255,0.08)',
          }}
        >
          <div className="flex items-center gap-3">
            <Target className="w-4 h-4 text-[#3D4F66]" />
            <p className="text-sm text-[#3D4F66]">No active goals — set one to track your progress</p>
          </div>
          <button
            onClick={() => setShowModal(true)}
            className="text-xs font-medium text-[#00D4AA] hover:text-[#00BF99] transition-colors flex-shrink-0 ml-4"
          >
            + Set goal
          </button>
        </div>
      </>
    );
  }

  return (
    <>
      {showModal && <AddGoalModal onClose={() => setShowModal(false)} />}

      <div
        className="rounded-xl p-5"
        style={{
          backgroundColor: 'rgba(255,255,255,0.03)',
          border: '1px solid rgba(255,255,255,0.06)',
        }}
      >
        {/* Header */}
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Target className="w-4 h-4 text-[#00D4AA]" />
            <h2 className="text-sm font-semibold text-[#8B97A8]">Active Goals</h2>
            <span className="text-xs text-[#3D4F66] bg-white/5 px-1.5 py-0.5 rounded-full">
              {goals.length}
            </span>
          </div>
          <button
            onClick={() => setShowModal(true)}
            className="w-6 h-6 rounded-md bg-[#00D4AA]/10 hover:bg-[#00D4AA]/20 flex items-center justify-center transition-colors"
            aria-label="Add goal"
          >
            <Plus className="w-3.5 h-3.5 text-[#00D4AA]" />
          </button>
        </div>

        {/* Goal list */}
        <div className="space-y-3">
          {goals.map((goal) => (
            <GoalRow key={goal.id} goal={goal} />
          ))}
        </div>

        {/* Achieved CTA if there are more than 3 */}
        {goals.length >= 3 && (
          <button
            onClick={() => setShowModal(true)}
            className="mt-4 w-full py-2 rounded-lg text-xs font-medium text-[#526380] hover:text-[#8B97A8] hover:bg-white/[0.03] transition-colors flex items-center justify-center gap-1.5"
          >
            <CheckCircle2 className="w-3.5 h-3.5" />
            Mark goals achieved to add new ones
          </button>
        )}
      </div>
    </>
  );
}
