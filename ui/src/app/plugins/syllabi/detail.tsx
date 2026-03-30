import { useEffect, useState } from "react"
import { useParams, useNavigate } from "react-router"
import {
    ArrowLeft, BookOpen, CheckCircle2, Circle, Clock,
    FileText, ChevronDown, ChevronRight
} from "lucide-react"
import { Card, CardContent, CardHeader } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { Progress } from "@/components/ui/progress"
import { getRequest } from "@/services"
import useStore from "@/store"

interface Chapter {
    id: number
    day: number
    topic: string
    task: string
    hours: number
    completed: boolean
    has_content: boolean
}

interface Week {
    week: number
    tasks: Chapter[]
}

interface Month {
    month: number
    weeks: Week[]
}

interface SyllabusDetail {
    skill_id: number
    skill: string
    email: string
    days: number
    hours: number
    created_at: string
    months: Month[]
}

function ChapterRow({ chapter }: { chapter: Chapter }) {
    const [expanded, setExpanded] = useState(false)

    return (
        <div
            className={`rounded-lg border transition-colors ${
                chapter.completed
                    ? "border-emerald-200 bg-emerald-50/40 dark:border-emerald-900/50 dark:bg-emerald-950/20"
                    : "border-border bg-card hover:bg-muted/30"
            }`}
        >
            <button
                className="flex w-full items-center gap-3 px-4 py-3 text-left"
                onClick={() => setExpanded((v) => !v)}
            >
                {chapter.completed ? (
                    <CheckCircle2 className="h-4 w-4 shrink-0 text-emerald-500" />
                ) : (
                    <Circle className="h-4 w-4 shrink-0 text-muted-foreground" />
                )}
                <span className="flex-1 text-sm font-medium leading-snug">
                    <span className="text-muted-foreground mr-2">Day {chapter.day}.</span>
                    {chapter.topic}
                </span>
                <div className="flex items-center gap-2 shrink-0">
                    {chapter.has_content && (
                        <FileText className="h-3.5 w-3.5 text-indigo-400" />
                    )}
                    <span className="flex items-center gap-1 text-xs text-muted-foreground">
                        <Clock className="h-3 w-3" />
                        {chapter.hours}h
                    </span>
                    {expanded
                        ? <ChevronDown className="h-4 w-4 text-muted-foreground" />
                        : <ChevronRight className="h-4 w-4 text-muted-foreground" />
                    }
                </div>
            </button>
            {expanded && (
                <div className="border-t border-border/50 px-4 py-3">
                    <p className="text-sm text-muted-foreground leading-relaxed">{chapter.task}</p>
                </div>
            )}
        </div>
    )
}

function WeekSection({ week }: { week: Week }) {
    const [open, setOpen] = useState(true)
    const completedCount = week.tasks.filter((t) => t.completed).length

    return (
        <div className="space-y-2">
            <button
                className="flex w-full items-center justify-between py-1 text-left"
                onClick={() => setOpen((v) => !v)}
            >
                <span className="text-sm font-semibold text-foreground/80">Week {week.week}</span>
                <div className="flex items-center gap-2">
                    <span className="text-xs text-muted-foreground">{completedCount}/{week.tasks.length} done</span>
                    {open
                        ? <ChevronDown className="h-3.5 w-3.5 text-muted-foreground" />
                        : <ChevronRight className="h-3.5 w-3.5 text-muted-foreground" />
                    }
                </div>
            </button>
            {open && (
                <div className="space-y-2 pl-1">
                    {week.tasks.map((chapter) => (
                        <ChapterRow key={chapter.id} chapter={chapter} />
                    ))}
                </div>
            )}
        </div>
    )
}

function MonthSection({ month }: { month: Month }) {
    const allTasks = month.weeks.flatMap((w) => w.tasks)
    const completedCount = allTasks.filter((t) => t.completed).length
    const progress = allTasks.length > 0 ? Math.round((completedCount / allTasks.length) * 100) : 0

    return (
        <Card className="overflow-hidden">
            <CardHeader className="pb-3 bg-muted/30">
                <div className="flex items-center justify-between gap-4">
                    <div className="flex items-center gap-2">
                        <div className="flex h-7 w-7 items-center justify-center rounded-md bg-primary text-primary-foreground text-xs font-bold">
                            {month.month}
                        </div>
                        <span className="font-semibold">Month {month.month}</span>
                    </div>
                    <div className="flex items-center gap-3">
                        <span className="text-xs text-muted-foreground">{completedCount}/{allTasks.length} days</span>
                        <Badge variant="outline" className="text-xs">{progress}%</Badge>
                    </div>
                </div>
                <Progress value={progress} className="h-1.5 mt-2" />
            </CardHeader>
            <CardContent className="pt-4 space-y-4">
                {month.weeks.map((week) => (
                    <WeekSection key={week.week} week={week} />
                ))}
            </CardContent>
        </Card>
    )
}

function DetailSkeleton() {
    return (
        <div className="p-6 space-y-6">
            <div className="flex items-center gap-3">
                <Skeleton className="h-8 w-8 rounded" />
                <Skeleton className="h-7 w-48" />
            </div>
            {[1, 2].map((i) => (
                <Card key={i} className="overflow-hidden">
                    <CardHeader className="bg-muted/30">
                        <div className="flex items-center gap-2">
                            <Skeleton className="h-7 w-7 rounded-md" />
                            <Skeleton className="h-5 w-24" />
                        </div>
                        <Skeleton className="h-1.5 w-full mt-2 rounded-full" />
                    </CardHeader>
                    <CardContent className="pt-4 space-y-2">
                        {[1, 2, 3, 4].map((j) => (
                            <Skeleton key={j} className="h-11 w-full rounded-lg" />
                        ))}
                    </CardContent>
                </Card>
            ))}
        </div>
    )
}

export default function SyllabusDetailPage() {
    const { skillId } = useParams<{ skillId: string }>()
    const navigate = useNavigate()
    const [detail, setDetail] = useState<SyllabusDetail | null>(null)
    const [loading, setLoading] = useState(true)
    const { setPluginName, setPluginInfo } = useStore((state: any) => state)

    useEffect(() => {
        async function fetchDetail() {
            const { success, data } = await getRequest(`/py/syllabi/${skillId}`)
            if (success) {
                setDetail(data)
                setPluginName(data.skill)
                setPluginInfo(`${data.email} · ${data.days} days`)
            }
            setLoading(false)
        }
        fetchDetail()
    }, [skillId])

    const allTasks = detail?.months.flatMap((m) => m.weeks.flatMap((w) => w.tasks)) ?? []
    const completedCount = allTasks.filter((t) => t.completed).length
    const overallProgress = allTasks.length > 0 ? Math.round((completedCount / allTasks.length) * 100) : 0

    if (loading) return <DetailSkeleton />

    if (!detail) return (
        <div className="p-6">
            <Button variant="ghost" size="sm" onClick={() => navigate("/syllabi")}>
                <ArrowLeft className="h-4 w-4 mr-1" /> Back
            </Button>
            <p className="mt-4 text-muted-foreground">Syllabus not found.</p>
        </div>
    )

    return (
        <div className="p-6 space-y-6">
            {/* header */}
            <div className="space-y-3">
                <Button variant="ghost" size="sm" className="-ml-2" onClick={() => navigate("/syllabi")}>
                    <ArrowLeft className="h-4 w-4 mr-1" /> All Syllabi
                </Button>
                <div className="flex items-start justify-between gap-4 flex-wrap">
                    <div className="flex items-center gap-3">
                        <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10 text-primary">
                            <BookOpen className="h-5 w-5" />
                        </div>
                        <div>
                            <h1 className="text-2xl font-bold tracking-tight">{detail.skill}</h1>
                            <p className="text-sm text-muted-foreground">{detail.email}</p>
                        </div>
                    </div>
                    <div className="flex items-center gap-4 text-sm text-muted-foreground">
                        <span className="flex items-center gap-1.5">
                            <Clock className="h-4 w-4" />
                            {detail.hours} hr/day · {detail.days} days
                        </span>
                        <Badge variant="outline" className="text-sm font-semibold">
                            {overallProgress}% complete
                        </Badge>
                    </div>
                </div>
                <div className="space-y-1">
                    <div className="flex justify-between text-xs text-muted-foreground">
                        <span>Overall progress</span>
                        <span>{completedCount} / {allTasks.length} chapters done</span>
                    </div>
                    <Progress value={overallProgress} className="h-2" />
                </div>
            </div>

            {/* months */}
            {detail.months.length === 0 ? (
                <Card className="flex flex-col items-center justify-center py-16 text-center border-dashed">
                    <BookOpen className="h-10 w-10 text-muted-foreground mb-3" />
                    <h3 className="font-semibold text-lg">No chapters yet</h3>
                    <p className="text-muted-foreground text-sm mt-1">Generate a syllabus to populate chapters.</p>
                </Card>
            ) : (
                <div className="space-y-4">
                    {detail.months.map((month) => (
                        <MonthSection key={month.month} month={month} />
                    ))}
                </div>
            )}
        </div>
    )
}
